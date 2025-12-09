"""SQL safety guardrails for tenant isolation and query validation."""

import re
from typing import Optional


class SQLGuardrails:
    """Validates SQL queries for safety and tenant isolation."""

    # Dangerous SQL keywords that should be blocked
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
        "EXECUTE_IMMEDIATE",
        "GRANT",
        "REVOKE",
        "MERGE",
    }

    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"--\s*$",  # SQL comments
        r"/\*.*?\*/",  # Multi-line comments
        r";\s*(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)",  # Multiple statements
        r"UNION\s+SELECT",  # Union-based injection
        r"OR\s+1\s*=\s*1",  # Always true conditions
        r"';?\s*(DROP|DELETE|TRUNCATE)",  # Statement termination
    ]

    def __init__(self, tenant_id: str):
        """
        Initialize SQL guardrails.

        Args:
            tenant_id: Tenant ID to enforce isolation
        """
        self.tenant_id = tenant_id

    def validate_query(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety and tenant isolation.

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        sql_upper = sql.upper().strip()

        # Check 1: Only SELECT queries allowed
        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        # Check 2: Block dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, sql_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # Check 3: Detect SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE | re.MULTILINE):
                return False, "Potential SQL injection detected"

        # Check 4: Ensure tenant isolation
        tenant_check = self._check_tenant_isolation(sql)
        if not tenant_check[0]:
            return tenant_check

        return True, None

    def _check_tenant_isolation(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Ensure SQL query includes tenant isolation.

        Args:
            sql: SQL query to check

        Returns:
            Tuple of (has_isolation, error_message)
        """
        sql_upper = sql.upper()
        
        # Sargon Partners uses 'accountId' as the tenant column
        tenant_column = "accountId"

        # Check for accountId in WHERE clause
        # Look for patterns like: WHERE ... accountId = ...
        where_pattern = rf"WHERE\s+.*?{tenant_column}\s*=\s*"
        
        # Also check for parameterized queries: WHERE accountId = :accountId or $1, etc.
        tenant_patterns = [
            rf"{tenant_column}\s*=\s*['\"]{re.escape(self.tenant_id)}['\"]",  # Literal value
            rf"{tenant_column}\s*=\s*:{tenant_column}",  # Named parameter
            rf"{tenant_column}\s*=\s*\$\d+",  # Positional parameter (PostgreSQL)
            rf"{tenant_column}\s*=\s*\?",  # Positional parameter (general)
            rf"{tenant_column}\s*=\s*%s",  # Python-style parameter
        ]

        # Check if WHERE clause exists
        if "WHERE" not in sql_upper:
            return False, f"Query must include a WHERE clause with {tenant_column} filter"

        # Check if any tenant isolation pattern matches
        has_tenant_filter = False
        for pattern in tenant_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                has_tenant_filter = True
                break

        # Also check if literal accountId value is present
        if f"'{self.tenant_id}'" in sql or f'"{self.tenant_id}"' in sql:
            # Check if it's near accountId
            if re.search(rf"{tenant_column}.*?['\"]{re.escape(self.tenant_id)}['\"]", sql, re.IGNORECASE):
                has_tenant_filter = True

        if not has_tenant_filter:
            return (
                False,
                f"Query must include tenant isolation: WHERE {tenant_column} = '{self.tenant_id}'",
            )

        return True, None

    def enforce_tenant_isolation(self, sql: str) -> str:
        """
        Enforce tenant isolation by adding/modifying WHERE clause.

        This should be used as a last resort if validation fails,
        but ideally queries should be generated with isolation already included.

        Args:
            sql: SQL query

        Returns:
            SQL query with enforced tenant isolation
        """
        sql_upper = sql.upper()
        tenant_column = "accountId"
        
        # If accountId filter already exists, return as-is
        tenant_patterns = [
            rf"{tenant_column}\s*=\s*['\"]{re.escape(self.tenant_id)}['\"]",
            rf"{tenant_column}\s*=\s*:{tenant_column}",
        ]
        
        for pattern in tenant_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return sql

        # Add tenant isolation to WHERE clause
        if "WHERE" in sql_upper:
            # Find WHERE clause and add accountId filter
            where_match = re.search(r"\bWHERE\b", sql_upper, re.IGNORECASE)
            if where_match:
                where_pos = where_match.end()
                # Insert accountId filter
                sql = (
                    sql[:where_pos]
                    + f" {tenant_column} = '{self.tenant_id}' AND"
                    + sql[where_pos:]
                )
        else:
            # Add WHERE clause at the end (before GROUP BY, ORDER BY, etc.)
            order_match = re.search(
                r"\b(ORDER BY|GROUP BY|HAVING|LIMIT)\b", sql_upper, re.IGNORECASE
            )
            if order_match:
                order_pos = order_match.start()
                sql = sql[:order_pos] + f" WHERE {tenant_column} = '{self.tenant_id}' " + sql[order_pos:]
            else:
                sql = sql.rstrip().rstrip(";") + f" WHERE {tenant_column} = '{self.tenant_id}'"

        return sql



