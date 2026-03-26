"""
AWS Bedrock client for generating chatbot responses and SQL queries
from natural language input.
"""

import json
import logging
import re
import time
import boto3
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any, Iterable

from app.config import settings
from app.logging.logger import get_logger, log_raw_model_output, set_request_context
from app.admin_config import get_prompt_template, get_llm_config, get_db_context


class BedrockClient:
    """Client for interacting with AWS Bedrock."""

    def __init__(self):
        self.logger = get_logger(__name__)

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
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        llm_config = get_llm_config()
        max_tokens = max_tokens if max_tokens is not None else llm_config["max_tokens"]
        temperature = temperature if temperature is not None else llm_config["temperature"]

        if request_id:
            set_request_context(request_id, tenant_id)

        system_blocks, messages = self._build_cached_messages(
            natural_language_query=natural_language_query,
            schema_context=schema_context,
            tenant_id=tenant_id,
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_blocks,
            "messages": messages,
        }

        try:
            start_time = time.time()

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            call_time_ms = (time.time() - start_time) * 1000

            try:
                from app.metrics import record_bedrock_call_time
                record_bedrock_call_time(call_time_ms)
            except Exception:
                pass

            response_body = json.loads(response["body"].read())

            text_content = self._extract_text(response_body)

            log_raw_model_output(self.logger, text_content)

            model_output = self._parse_model_json(text_content)

            mode = model_output.get("mode", "sql")
            sql = model_output.get("sql")

            sql_length = len(sql) if sql else 0
            self.logger.info(
                f"Parsed model output | mode={mode} | sql_length={sql_length}"
            )

            return {
                "mode": mode,
                "response": model_output.get("response"),
                "sql": sql,
                "explanation": model_output.get("explanation"),
                "model_id": self.model_id,
                "usage": response_body.get("usage", {}),
            }

        except ClientError as e:
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            self.logger.error(f"Bedrock API error: {error_msg}")
            raise RuntimeError(f"Bedrock API error: {error_msg}") from e

    def generate_sql_stream(
        self,
        natural_language_query: str,
        schema_context: str,
        tenant_id: str,
        max_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> Iterable[Dict[str, Any]]:
        """
        Streaming variant of generate_sql.

        Yields dict events of the form:
        - {"event": "thinking", "text": "..."}   # incremental reasoning
        - {"event": "final", "result": {...}}    # final parsed JSON result dict
        """
        llm_config = get_llm_config()
        max_tokens = max_tokens if max_tokens is not None else llm_config["max_tokens"]

        if request_id:
            set_request_context(request_id, tenant_id)

        system_blocks, messages = self._build_cached_messages(
            natural_language_query=natural_language_query,
            schema_context=schema_context,
            tenant_id=tenant_id,
        )

        # Enable extended thinking for supported Claude models.
        thinking_budget = min(max_tokens // 2 if max_tokens else 1024, 4000) or 1024

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            # NOTE: When thinking is enabled, Anthropic recommends not using temperature/top_p/top_k.
            "thinking": {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            },
            "system": system_blocks,
            "messages": messages,
        }

        start_time = time.time()
        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            call_time_ms = (time.time() - start_time) * 1000
            try:
                from app.metrics import record_bedrock_call_time

                record_bedrock_call_time(call_time_ms)
            except Exception:
                pass

            accumulated_text = ""
            input_tokens = 0
            output_tokens = 0
            cache_read_tokens = 0
            cache_write_tokens = 0

            for event in response.get("body", []):
                chunk = event.get("chunk")
                if not chunk:
                    continue

                payload_bytes = chunk.get("bytes")
                if not payload_bytes:
                    continue

                try:
                    payload_str = payload_bytes.decode("utf-8")
                    payload = json.loads(payload_str)
                except Exception:
                    # If we can't parse a chunk, skip it but keep streaming.
                    continue

                event_type = payload.get("type")

                # Capture token counts from message_start (includes cache stats)
                if event_type == "message_start":
                    usage = payload.get("message", {}).get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                    cache_read_tokens = usage.get("cache_read_input_tokens", 0)
                    cache_write_tokens = usage.get("cache_creation_input_tokens", 0)

                # Capture output token count from message_delta
                elif event_type == "message_delta":
                    usage = payload.get("usage", {})
                    output_tokens = usage.get("output_tokens", 0)

                # Thinking deltas
                elif event_type == "content_block_delta":
                    delta = payload.get("delta", {})
                    delta_type = delta.get("type")

                    if delta_type == "thinking_delta":
                        thinking_text = delta.get("thinking", "")
                        if thinking_text:
                            yield {"event": "thinking", "text": thinking_text}

                    elif delta_type == "text_delta":
                        text = delta.get("text", "")
                        if text:
                            accumulated_text += text

                # End of message
                if event_type == "message_stop":
                    break

            if not accumulated_text:
                raise RuntimeError("Model did not return any text in streaming response")

            log_raw_model_output(self.logger, accumulated_text)
            model_output = self._parse_model_json(accumulated_text)

            mode = model_output.get("mode", "sql")
            sql = model_output.get("sql")
            sql_length = len(sql) if sql else 0
            self.logger.info(
                f"Parsed streaming model output | mode={mode} | sql_length={sql_length}"
            )

            self.logger.info(
                f"Token usage | input={input_tokens} output={output_tokens} "
                f"cache_read={cache_read_tokens} cache_write={cache_write_tokens}"
            )

            result = {
                "mode": mode,
                "response": model_output.get("response"),
                "sql": sql,
                "explanation": model_output.get("explanation"),
                "model_id": self.model_id,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_input_tokens": cache_read_tokens,
                    "cache_creation_input_tokens": cache_write_tokens,
                },
            }

            yield {"event": "final", "result": result}

        except ClientError as e:
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            self.logger.error(f"Bedrock streaming API error: {error_msg}")
            raise RuntimeError(f"Bedrock streaming API error: {error_msg}") from e

    # ==========================================================
    # Data validation through prompting
    # ==========================================================

    def validate_results(
        self,
        original_query: str,
        generated_sql: str,
        results: List[dict],
        tenant_id: str,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Validate that the query results actually match the user's original question.
        
        This is a second Bedrock call that checks if the returned data
        is relevant and correct for the question asked.
        
        Returns dict with:
        - status: 'valid' | 'partial' | 'mismatch'
        - reasoning: explanation of the validation result
        """
        if max_tokens is None:
            max_tokens = get_llm_config().get("validation_max_tokens", 1024)
        # Format results as a readable sample
        results_sample = json.dumps(results[:10], indent=2, default=str)
        
        validation_prompt = f"""
You are a data validation assistant. Your job is to verify that SQL query results 
actually answer the user's original question.

Original user question:
"{original_query}"

Generated SQL:
{generated_sql}

Query results (first {min(len(results), 10)} rows):
{results_sample}

Evaluate whether the results correctly and completely answer the user's question.

Consider:
1. Do the columns returned match what the user asked for?
2. Do the filter conditions match the user's intent?
3. Is the data format appropriate for the question?
4. Are there any obvious errors or missing data?

Return JSON in exactly this format:
{{
  "status": "valid | partial | mismatch",
  "reasoning": "Brief explanation of your assessment"
}}

Rules:
- "valid" = results fully answer the question
- "partial" = results partially answer but may be missing something 
- "mismatch" = results don't match what was asked
- Your response MUST be valid JSON only
- Start with '{{' and end with '}}'
""".strip()

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "messages": [
                {"role": "user", "content": validation_prompt}
            ],
        }

        try:
            start_time = time.time()
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            call_time_ms = (time.time() - start_time) * 1000
            self.logger.info(f"Validation call completed in {call_time_ms:.0f}ms")

            response_body = json.loads(response["body"].read())
            text_content = self._extract_text(response_body)

            # Parse the validation JSON
            match = re.search(r"\{.*\}", text_content, re.DOTALL)
            if not match:
                return {"status": "skipped", "reasoning": "Could not parse validation response"}

            result = json.loads(match.group())
            return {
                "status": result.get("status", "unknown"),
                "reasoning": result.get("reasoning", "No reasoning provided"),
            }

        except Exception as e:
            self.logger.warning(f"Validation call failed: {e}")
            return {"status": "skipped", "reasoning": f"Validation error: {str(e)}"}

    # ==========================================================
    # Prompt construction
    # ==========================================================

    def _build_cached_messages(
        self,
        natural_language_query: str,
        schema_context: str,
        tenant_id: str,
    ) -> tuple:
        """
        Returns (system_blocks, messages) with prompt cache markers.

        Cache layout:
          system_blocks[0]  — static instructions, cached globally
          messages[0][0]    — schema + tenant context, cached per tenant/schema
          messages[0][1]    — user query, always dynamic (no cache marker)
        """
        db_context_str = get_db_context() or ""
        custom = get_prompt_template()

        if custom and custom.strip():
            # For custom templates, split on {natural_language_query} so the
            # static prefix is cached and only the query itself is dynamic.
            rendered_prefix = (
                custom.replace("{schema_context}", schema_context)
                .replace("{tenant_id}", tenant_id)
                .replace("{db_context}", db_context_str)
            )
            if "{db_context}" not in custom and db_context_str.strip():
                rendered_prefix = (
                    rendered_prefix.rstrip()
                    + "\n\nAdditional database context (from administrator):\n"
                    + db_context_str.strip()
                )

            if "{natural_language_query}" in rendered_prefix:
                parts = rendered_prefix.split("{natural_language_query}", 1)
                system_blocks = [
                    {"type": "text", "text": parts[0].strip(), "cache_control": {"type": "ephemeral"}}
                ]
                user_content = [
                    {"type": "text", "text": f"{natural_language_query}{parts[1]}"}
                ]
            else:
                # No placeholder found — treat whole template as cached context
                system_blocks = [
                    {"type": "text", "text": rendered_prefix.strip(), "cache_control": {"type": "ephemeral"}}
                ]
                user_content = [
                    {"type": "text", "text": natural_language_query}
                ]

            messages = [{"role": "user", "content": user_content}]
            return system_blocks, messages

        # --- Default prompt ---
        static_instructions = """You are an AI assistant for an asset-tracking system.

Decide how to respond to the user's message.

Choose ONE mode:
- chat: greetings or general questions
- clarification: request is ambiguous or missing details
- sql: request clearly asks for data

When responding:
- Be helpful and concise.
- Use natural language.

CRITICAL OUTPUT RULES:
- The response MUST be valid JSON.
- Do NOT include any text outside the JSON object.
- All string values MUST be single-line.
- The sql field MUST be a single-line string or null.
- Do NOT include markdown, code fences, or explanations.

SQL rules (only if mode is sql):
- Generate a SELECT query only.
- Use the schema provided.
- The tenant filter (accountId) is specified in the context block below.
- IMPORTANT: In SELECT columns, use human-friendly identifiers instead of cloudUUID:
  - Use serialNumber or description to identify assets/tags
  - If cloudUUID is needed for joins, use it internally but alias it as asset_number in the output
  - Example: SELECT T.serialNumber AS asset_number, T.description, ... instead of SELECT T.cloudUUID, ...
  - Do NOT include accountId in the SELECT output columns
  - Do NOT include cloudUUID as a visible output column

Return JSON in exactly this format:
{
  "mode": "chat | clarification | sql",
  "response": "Natural language response",
  "sql": "SQL query if mode is sql, otherwise null"
}

IMPORTANT: Your response must start with '{' and end with '}'. If you include any text outside the JSON object, the request will fail."""

        extra_block = ""
        if db_context_str.strip():
            extra_block = f"\n\nAdditional database context (from administrator):\n{db_context_str.strip()}"

        schema_block = f"Tenant filter: Always include WHERE accountId = '{tenant_id}' in SQL queries.\n\nDatabase schema:\n{schema_context}{extra_block}"

        system_blocks = [
            {"type": "text", "text": static_instructions, "cache_control": {"type": "ephemeral"}}
        ]

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": schema_block, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": f"User input:\n{natural_language_query}"},
                ],
            }
        ]

        return system_blocks, messages

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

    def _parse_model_json(self, text_content: str) -> dict:
        """
        Extract and parse the JSON object from the model's text output.
        """
        try:
            match = re.search(r"\{.*\}", text_content, re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in model output")

            return json.loads(match.group())

        except Exception as e:
            self.logger.error(
                "Model did not return valid JSON after extraction. "
                f"Raw output (first 500 chars): {text_content[:500]}"
            )
            raise RuntimeError("Model did not return valid JSON") from e
