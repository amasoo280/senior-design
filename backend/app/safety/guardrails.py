"""SQL safety guardrails for tenant isolation and query validation."""

import re
from typing import Optional


class SQLGuardrails:
    """Validates SQL queries for safety and strict tenant isolation."""

    # Explicitly allowed tenant IDs (test database only)
    ALLOWED_TENANT_IDS = {
        "c55b3c70-7aa7-11eb-a7e8-9b4baf296adf",
        "eaeddcf1-fb98-11eb-94c9-b1e578657155",
    }

    # Dangerous SQL keywords that must never appear
    DANGEROUS_KEYWORDS = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "EXEC",
        "EXECUTE",
        "MERGE",
        "GRANT",
        "REVOKE",
    }

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"--",                  # Inline comments
        r"/\*.*?\*/",            # Block comments
        r";\s*\w+",              # Multiple statements
        r"\bUNION\b\s+\bSELECT\b",
        r"\bOR\b\s+1\s*=\s*1",
    ]

    TENANT_COLUMN = "accountId"

    def __init__(self, tenant_id: str):
        """
        Initialize SQL guardrails.

        Args:
            tenant_id: Tenant ID provided by authenticated context
        """
        if tenant_id not in self.ALLOWED_TENANT_IDS:
            raise ValueError(f"Invalid tenant_id: {tenant_id}")

        self.tenant_id = tenant_id

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
        for keyword in self.DANGEROUS_KEYWORDS:
            if re.search(rf"\b{keyword}\b", sql_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # 3. Detect SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
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

        if "WHERE" not in sql_upper:
            return (
                False,
                f"Query must include a WHERE clause filtering on {self.TENANT_COLUMN}",
            )

        # Acceptable tenant filter forms
        tenant_patterns = [
            rf"{self.TENANT_COLUMN}\s*=\s*['\"]{re.escape(self.tenant_id)}['\"]",
            rf"{self.TENANT_COLUMN}\s*=\s*:{self.TENANT_COLUMN}",
            rf"{self.TENANT_COLUMN}\s*=\s*\?",
            rf"{self.TENANT_COLUMN}\s*=\s*%s",
        ]

        for pattern in tenant_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True, None

        return (
            False,
            (
                f"Missing or invalid tenant isolation. "
                f"Query must include: WHERE {self.TENANT_COLUMN} = '{self.tenant_id}'"
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
            rf"{self.TENANT_COLUMN}\s*=\s*['\"]{re.escape(self.tenant_id)}['\"]",
            sql_clean,
            re.IGNORECASE,
        ):
            return sql_clean

        # Inject tenant filter
        if "WHERE" in sql_upper:
            return re.sub(
                r"\bWHERE\b",
                f"WHERE {self.TENANT_COLUMN} = '{self.tenant_id}' AND",
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
                + f" WHERE {self.TENANT_COLUMN} = '{self.tenant_id}' "
                + sql_clean[idx:]
            )

        return sql_clean + f" WHERE {self.TENANT_COLUMN} = '{self.tenant_id}'"
