"""AWS Bedrock client for generating SQL queries from natural language."""

import json
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError


class BedrockClient:
    """Client for interacting with AWS Bedrock to generate SQL queries."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """
        Initialize Bedrock client.

        Args:
            model_id: Bedrock model ID (default: anthropic.claude-3-sonnet-20240229-v1:0)
            region_name: AWS region (default: us-east-1)
            aws_access_key_id: AWS access key (from env if not provided)
            aws_secret_access_key: AWS secret key (from env if not provided)
        """
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"
        )
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

        # Initialize Bedrock runtime client
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region_name,
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key
            or os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def generate_sql(
        self,
        natural_language_query: str,
        schema_context: str,
        tenant_id: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> dict:
        """
        Generate SQL query from natural language using Bedrock.

        Args:
            natural_language_query: User's natural language question
            schema_context: Database schema context for the prompt
            tenant_id: Tenant ID for tenant isolation
            max_tokens: Maximum tokens in response (default: 4096)
            temperature: Sampling temperature (default: 0.1 for deterministic SQL)

        Returns:
            dict with 'sql' and 'explanation' keys, or raises exception

        Raises:
            ClientError: If Bedrock API call fails
            ValueError: If response is invalid
        """
        # Build the prompt for Claude
        prompt = self._build_prompt(natural_language_query, schema_context, tenant_id)

        # Prepare request body for Claude 3
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        try:
            # Invoke Bedrock model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            # Parse response
            response_body = json.loads(response.get("body").read())
            
            # Extract text from Claude's response
            text_content = ""
            for content_block in response_body.get("content", []):
                if content_block.get("type") == "text":
                    text_content += content_block.get("text", "")

            if not text_content:
                raise ValueError("Empty response from Bedrock model")

            # Parse SQL and explanation from response
            sql, explanation = self._parse_response(text_content)

            return {
                "sql": sql,
                "explanation": explanation,
                "model_id": self.model_id,
                "usage": response_body.get("usage", {}),
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            raise ClientError(
                {
                    "Error": {
                        "Code": error_code,
                        "Message": f"Bedrock API error: {error_message}",
                    }
                },
                "InvokeModel",
            )

    def _build_prompt(
        self, natural_language_query: str, schema_context: str, tenant_id: str
    ) -> str:
        """
        Build the prompt for Claude to generate SQL.

        Args:
            natural_language_query: User's natural language question
            schema_context: Database schema context
            tenant_id: Tenant ID for isolation

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert SQL generator that converts natural language queries to safe, optimized SQL.

CRITICAL REQUIREMENTS:
1. Generate ONLY valid SQL SELECT queries (no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE)
2. ALL queries MUST include tenant isolation: WHERE tenant_id = '{tenant_id}'
3. Use parameterized queries or ensure tenant_id is properly quoted
4. Do not generate queries that could modify or delete data
5. Ensure SQL is safe from SQL injection attacks
6. Return only the SQL query in a code block labeled "SQL", followed by a brief explanation

DATABASE SCHEMA:
{schema_context}

USER QUESTION:
{natural_language_query}

Generate a safe SQL SELECT query that:
- Answers the user's question
- Includes tenant isolation with tenant_id = '{tenant_id}'
- Uses proper SQL syntax
- Is optimized for performance

Return your response in this exact format:

SQL:
```sql
SELECT ...
```

EXPLANATION:
[Brief explanation of what the query does]
"""

    def _parse_response(self, response_text: str) -> tuple[str, str]:
        """
        Parse SQL and explanation from Claude's response.

        Args:
            response_text: Raw response text from Claude

        Returns:
            Tuple of (sql_query, explanation)
        """
        sql = ""
        explanation = ""

        # Try to extract SQL from code block
        sql_block_start = response_text.find("```sql")
        if sql_block_start != -1:
            sql_block_start = response_text.find("\n", sql_block_start) + 1
            sql_block_end = response_text.find("```", sql_block_start)
            if sql_block_end != -1:
                sql = response_text[sql_block_start:sql_block_end].strip()

        # If no SQL block found, try to find SQL: marker
        if not sql:
            sql_marker = response_text.find("SQL:")
            if sql_marker != -1:
                sql_start = response_text.find("\n", sql_marker) + 1
                # Look for next section or end
                explanation_marker = response_text.find("EXPLANATION:", sql_start)
                if explanation_marker != -1:
                    sql = response_text[sql_start:explanation_marker].strip()
                else:
                    sql = response_text[sql_start:].strip()

        # Extract explanation
        explanation_marker = response_text.find("EXPLANATION:")
        if explanation_marker != -1:
            explanation = response_text[explanation_marker + len("EXPLANATION:"):].strip()

        # Clean up SQL (remove markdown code blocks if still present)
        sql = sql.replace("```sql", "").replace("```", "").strip()

        if not sql:
            raise ValueError("Could not extract SQL from Bedrock response")

        return sql, explanation or "Generated SQL query from natural language."



