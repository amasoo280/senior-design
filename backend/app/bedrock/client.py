"""
AWS Bedrock client for generating chatbot responses and SQL queries
from natural language input.
"""

import json
import boto3
from botocore.exceptions import ClientError

from app.config import settings


class BedrockClient:
    """Client for interacting with AWS Bedrock."""

    def __init__(self):
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
    ) -> dict:
        """
        Generate a response from Bedrock.

        Returns a dict with:
          - mode: chat | clarification | sql
          - response: user-facing message
          - sql: SQL string if mode == sql
          - explanation: internal explanation (not for users)
        """

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
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())

            # Extract text from Claude response blocks
            text_content = self._extract_text(response_body)

            # Parse structured JSON from the model
            try:
                model_output = json.loads(text_content)
            except json.JSONDecodeError:
                raise RuntimeError(
                    "Model did not return valid JSON.\n"
                    f"Raw output:\n{text_content}"
                )

            return {
                "mode": model_output.get("mode", "sql"),
                "response": model_output.get("response"),
                "sql": model_output.get("sql"),
                "explanation": model_output.get("explanation"),
                "model_id": self.model_id,
                "usage": response_body.get("usage", {}),
            }

        except ClientError as e:
            error_msg = e.response.get("Error", {}).get("Message", str(e))
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
