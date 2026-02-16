"""SQL safety guardrails for tenant isolation and query validation."""

import re
from typing import Optional

from app.admin_config import get_guardrails_config


class SQLGuardrails:
    """Validates SQL queries for safety and strict tenant isolation. Uses admin-configurable rules."""

    def __init__(self, tenant_id: str):
        """
        Initialize SQL guardrails from current admin config.

        Args:
            tenant_id: Tenant ID provided by authenticated context
        """
        cfg = get_guardrails_config()
        self._allowed_tenant_ids = set(cfg.get("allowed_tenant_ids", []))
        self._dangerous_keywords = set((k or "").strip().upper() for k in cfg.get("dangerous_keywords", []) if k)
        self._sql_injection_patterns = list(cfg.get("sql_injection_patterns", []))
        self._tenant_column = (cfg.get("tenant_column") or "accountId").strip()
        self.tenant_id = tenant_id

        if self.tenant_id not in self._allowed_tenant_ids:
            raise ValueError(f"Invalid tenant_id: {tenant_id}")

    def validate_query(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety and tenant isolation.

        Args:
            sql: SQL query to validate

        Returns:
            (is_valid, error_message)
        """
        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # 1. Only SELECT queries allowed
        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        # 2. Block dangerous keywords anywhere in query
        for keyword in self._dangerous_keywords:
            if keyword and re.search(rf"\b{re.escape(keyword)}\b", sql_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # 3. Detect SQL injection patterns
        for pattern in self._sql_injection_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE | re.DOTALL):
                return False, "Potential SQL injection detected"

        # 4. Enforce strict tenant isolation
        tenant_check = self._check_tenant_isolation(sql_clean)
        if not tenant_check[0]:
            return tenant_check

        return True, None

    def _check_tenant_isolation(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Ensure query contains a valid tenant filter using accountId.

        Args:
            sql: SQL query

        Returns:
            (has_isolation, error_message)
        """
        sql_upper = sql.upper()
        col = self._tenant_column

        if "WHERE" not in sql_upper:
            return (
                False,
                f"Query must include a WHERE clause filtering on {col}",
            )

        # Acceptable tenant filter forms
        tenant_patterns = [
            rf"{re.escape(col)}\s*=\s*['\"]{re.escape(self.tenant_id)}['\"]",
            rf"{re.escape(col)}\s*=\s*:{col}",
            rf"{re.escape(col)}\s*=\s*\?",
            rf"{re.escape(col)}\s*=\s*%s",
        ]

        for pattern in tenant_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True, None

        return (
            False,
            (
                f"Missing or invalid tenant isolation. "
                f"Query must include: WHERE {self._tenant_column} = '{self.tenant_id}'"
            ),
        )

    def enforce_tenant_isolation(self, sql: str) -> str:
        """
        Enforce tenant isolation by injecting accountId filter.

        This should be a fallback only. Ideally, the model generates
        tenant-safe SQL by design.

        Args:
            sql: SQL query

        Returns:
            SQL query with enforced tenant isolation
        """
        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # If tenant filter already exists, return as-is
        if re.search(
            rf"{re.escape(self._tenant_column)}\s*=\s*['\"]{re.escape(self.tenant_id)}['\"]",
            sql_clean,
            re.IGNORECASE,
        ):
            return sql_clean

        # Inject tenant filter
        if "WHERE" in sql_upper:
            return re.sub(
                r"\bWHERE\b",
                f"WHERE {self._tenant_column} = '{self.tenant_id}' AND",
                sql_clean,
                count=1,
                flags=re.IGNORECASE,
            )

        # Insert WHERE before ORDER/GROUP/LIMIT
        match = re.search(
            r"\b(ORDER BY|GROUP BY|HAVING|LIMIT)\b",
            sql_upper,
            re.IGNORECASE,
        )
        if match:
            idx = match.start()
            return (
                sql_clean[:idx]
                + f" WHERE {self._tenant_column} = '{self.tenant_id}' "
                + sql_clean[idx:]
            )

        return sql_clean + f" WHERE {self._tenant_column} = '{self.tenant_id}'"
