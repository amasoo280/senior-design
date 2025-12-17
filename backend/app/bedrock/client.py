"""
AWS Bedrock client for generating chatbot responses and SQL queries
from natural language input.
"""

import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional

from app.config import settings
from app.logging.logger import get_logger, log_raw_model_output, set_request_context


class BedrockClient:
    """Client for interacting with AWS Bedrock."""

    def __init__(self):
        # Get logger for this module
        self.logger = get_logger(__name__)
        # Validate required settings
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise ValueError(
                "AWS credentials missing. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
            )

        if not settings.aws_region:
            raise ValueError("AWS_REGION is missing in .env")

        if not settings.bedrock_model_id:
            raise ValueError(
                "BEDROCK_MODEL_ID is missing in .env. "
                "Example: us.anthropic.claude-3-sonnet-20240229-v1:0"
            )

        self.model_id = settings.bedrock_model_id.strip()
        self.region = settings.aws_region

        # Bedrock Runtime client
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=settings.aws_access_key_id.strip(),
            aws_secret_access_key=settings.aws_secret_access_key.strip(),
        )

    # ==========================================================
    # Public method
    # ==========================================================

    def generate_sql(
        self,
        natural_language_query: str,
        schema_context: str,
        tenant_id: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Generate a response from Bedrock.

        Returns a dict with:
          - mode: chat | clarification | sql
          - response: user-facing message
          - sql: SQL string if mode == sql
          - explanation: internal explanation (not for users)
        """
        # Set request context for logging if provided
        if request_id:
            set_request_context(request_id, tenant_id)

        prompt = self._build_prompt(
            natural_language_query=natural_language_query,
            schema_context=schema_context,
            tenant_id=tenant_id,
        )

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
            import time
            start_time = time.time()
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            call_time_ms = (time.time() - start_time) * 1000
            
            # Track metrics: record Bedrock call time
            try:
                from app.metrics import record_bedrock_call_time
                record_bedrock_call_time(call_time_ms)
            except Exception:
                pass  # Don't break if metrics tracking fails

            response_body = json.loads(response["body"].read())

            # Extract text from Claude response blocks
            text_content = self._extract_text(response_body)

            # Log: Raw model output (truncated, only at DEBUG level)
            # This helps debug LLM output issues without cluttering INFO logs
            log_raw_model_output(self.logger, text_content)

            # Parse structured JSON from the model
            try:
                model_output = json.loads(text_content)
            except json.JSONDecodeError:
                # Log: Error parsing JSON from model (ERROR level)
                self.logger.error(f"Model did not return valid JSON. Raw output (first 500 chars): {text_content[:500]}")
                raise RuntimeError(
                    "Model did not return valid JSON.\n"
                    f"Raw output:\n{text_content}"
                )

            # Extract parsed output
            mode = model_output.get("mode", "sql")
            sql = model_output.get("sql")
            
            # Log: Parsed model output (mode and SQL length for debugging)
            sql_length = len(sql) if sql else 0
            self.logger.info(f"Parsed model output | mode={mode} | sql_length={sql_length}")

            return {
                "mode": mode,
                "response": model_output.get("response"),
                "sql": sql,
                "explanation": model_output.get("explanation"),
                "model_id": self.model_id,
                "usage": response_body.get("usage", {}),
            }

        except ClientError as e:
            # Log: Bedrock API errors (ERROR level)
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            self.logger.error(f"Bedrock API error: {error_msg}")
            raise RuntimeError(f"Bedrock API error: {error_msg}") from e

    # ==========================================================
    # Prompt construction
    # ==========================================================

    def _build_prompt(
    self,
    natural_language_query: str,
    schema_context: str,
    tenant_id: str,
    ) -> str:
        return f"""
You are an AI assistant for an asset-tracking system.

Decide how to respond to the user's message.

Choose ONE mode:
- chat: greetings or general questions
- clarification: request is ambiguous or missing details
- sql: request clearly asks for data

When responding:
- Be helpful and concise.
- It's okay to briefly explain what you're doing.
- Use natural language.

CRITICAL OUTPUT RULES (MUST FOLLOW):
- The response MUST be valid JSON.
- Do NOT include any text outside the JSON object.
- All string values MUST be single-line (no newlines).
- The "sql" field MUST be a single-line string.
- Do NOT include formatting, comments, or stray words inside the SQL.
- Do NOT include markdown or code fences.


SQL rules (only if mode = "sql"):
- Generate a SELECT query only.
- Use the schema provided.
- Always filter by accountId = "{tenant_id}".

Return valid JSON in this format:
{{
  "mode": "chat | clarification | sql",
  "response": "Natural language response",
  "sql": "SQL query if mode is sql, otherwise null"
}}

Database schema:
{schema_context}

User input:
{natural_language_query}
""".strip()



    # ==========================================================
    # Response parsing helpers
    # ==========================================================

    def _extract_text(self, response_body: dict) -> str:
        """
        Extract text content from Claude-style Bedrock responses.
        """
        text = ""
        for block in response_body.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        text = text.strip()
        if not text:
            raise ValueError("Model returned no text content")

        return text
