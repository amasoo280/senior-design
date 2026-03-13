import logging
import json
import time
from typing import Optional, List, Any

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

from app.bedrock.client import BedrockClient
from app.config import settings
from app.executor.executor import execute_query, DatabaseExecutionError
from app.logging.logger import (
    get_logger,
    log_request_start,
    log_request_end,
    set_request_context,
    safe_log_sql,
    safe_truncate,
)
from app.logging import get_logs
from app.metrics import (
    get_metrics,
    get_metrics_by_tenant,
    get_all_tenant_ids,
    increment_request_count,
    increment_error_count,
    increment_sql_query_count,
    increment_chat_count,
    increment_clarification_count,
    record_query_execution_time,
    record_bedrock_call_time,
)
from app.safety.guardrails import SQLGuardrails
from app.schema.context import SchemaContext

# Auth0 authentication
from app.auth import get_current_user, get_optional_user, require_admin
from app.admin_config import (
    get_guardrails_config,
    set_guardrails_config,
    get_prompt_template,
    set_prompt_template,
    get_llm_config,
    set_llm_config,
)

# Get structured logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title="Sargon Partners AI Chatbot API",
    description="Natural language to SQL query API powered by AWS Bedrock",
    version="1.0.0"
)

# Configure CORS - allow frontend URL from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
bedrock_client = BedrockClient()
schema_context = SchemaContext()


# ============================================
# Request/Response Models
# ============================================

class AskRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (optional if provided in header)")
    execute: bool = Field(False, description="Whether to execute the generated SQL query")

class AskResponse(BaseModel):
    sql: str
    explanation: Optional[str] = None
    natural_language_query: str
    tenant_id: str
    validated: bool
    rows: Optional[List[Any]] = None
    row_count: Optional[int] = None
    execution_error: Optional[str] = None
    validation_status: Optional[str] = None
    validation_reasoning: Optional[str] = None

# ============================================
# Root / Health / System Endpoints
# ============================================

@app.get("/")
def root():
    return {
        "name": "Sargon Partners AI Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/auth/me": "GET - Get current user info (Auth0)",
            "/auth/verify": "GET - Verify Auth0 token",
            "/ask": "POST - Convert natural language to SQL",
            "/ask/stream": "POST - Convert natural language to SQL (streaming)",
            "/health": "GET - Health check",
            "/db-ping": "GET - Database connection test",
            "/logs": "GET - View application logs (auth required)",
            "/analytics": "GET - Get analytics and metrics (auth required)",
            "/admin/config/guardrails": "GET/PUT - Guardrails config (admin)",
            "/admin/config/prompt": "GET/PUT - LLM prompt template (admin)",
            "/admin/config/llm": "GET/PUT - LLM params e.g. max_tokens (admin)",
            "/admin/metrics": "GET - Full metrics + by-tenant (admin)",
            "/admin/metrics/accounts": "GET - List tenant IDs (admin)",
            "/admin/metrics/account/{tenant_id}": "GET - Per-account metrics (admin)",
            "/admin/logs": "GET - Logs, optional tenant_id filter (admin)",
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/db-ping")
def db_ping():
    """Test database connection."""
    try:
        rows = execute_query("SELECT 1 AS ok;")
        return {"status": "ok", "result": rows}
    except DatabaseExecutionError as exc:
        logger.error(f"Database ping failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


# ============================================
# Authentication Endpoints (Auth0)
# ============================================

@app.get("/auth/me")
def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid Auth0 JWT token in Authorization header.
    Includes is_admin for frontend to show/hide admin features.
    """
    permissions = user.get("permissions", [])
    email = user.get("email", "unknown")
    is_admin = (
        "admin" in permissions
        or "admin:all" in permissions
        or (settings.admin_emails and email.lower() in [e.lower().strip() for e in settings.admin_emails])
    )
    return {"user": {**user, "is_admin": is_admin}}

@app.get("/auth/verify")
def verify_auth(user: dict = Depends(get_current_user)):
    """Verify if current Auth0 token is valid and return user info."""
    return {"authenticated": True, "user": user}

@app.post("/auth/logout")
def logout(user: dict = Depends(get_current_user)):
    """
    Logout current user.
    Note: With Auth0, logout is primarily handled client-side.
    This endpoint is provided for logging purposes.
    """
    logger.info(f"User logged out: {user.get('email', 'unknown')}")
    return {"message": "Logged out successfully"}


# ============================================
# Logs & Analytics Endpoints
# ============================================

@app.get("/logs")
def get_application_logs(
    limit: int = 100,
    level: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get recent application logs for viewing in the web interface.
    """
    limit = min(limit, 500)
    logs = get_logs(limit=limit, level=level, tenant_id=tenant_id)
    return {
        "logs": logs,
        "count": len(logs),
        "total_available": len(logs),
    }

@app.get("/analytics")
def get_analytics(user: dict = Depends(get_current_user)):
    """Get analytics and metrics data for the dashboard."""
    return get_metrics()


# ============================================
# Admin-only Endpoints
# ============================================

@app.get("/admin/config/guardrails")
def admin_get_guardrails():
    """Get current guardrails configuration (TEMP: open during testing)."""
    return get_guardrails_config()


class GuardrailsUpdate(BaseModel):
    allowed_tenant_ids: Optional[List[str]] = None
    dangerous_keywords: Optional[List[str]] = None
    sql_injection_patterns: Optional[List[str]] = None
    tenant_column: Optional[str] = None


@app.put("/admin/config/guardrails")
def admin_update_guardrails(body: GuardrailsUpdate):
    """Update guardrails configuration (TEMP: open during testing)."""
    config = {}
    if body.allowed_tenant_ids is not None:
        config["allowed_tenant_ids"] = body.allowed_tenant_ids
    if body.dangerous_keywords is not None:
        config["dangerous_keywords"] = body.dangerous_keywords
    if body.sql_injection_patterns is not None:
        config["sql_injection_patterns"] = body.sql_injection_patterns
    if body.tenant_column is not None:
        config["tenant_column"] = body.tenant_column
    return set_guardrails_config(config)


@app.get("/admin/config/prompt")
def admin_get_prompt():
    """Get current LLM prompt template (TEMP: open during testing). None = use built-in."""
    return {"prompt_template": get_prompt_template()}


class PromptUpdate(BaseModel):
    prompt_template: Optional[str] = None


@app.put("/admin/config/prompt")
def admin_update_prompt(body: PromptUpdate):
    """Update LLM prompt template (TEMP: open during testing). Set to null/empty to use built-in."""
    set_prompt_template(body.prompt_template if body.prompt_template else None)
    return {"prompt_template": get_prompt_template()}


@app.get("/admin/config/llm")
def admin_get_llm():
    """Get LLM parameters: max_tokens, temperature, etc. (TEMP: open during testing)."""
    return get_llm_config()


class LLMUpdate(BaseModel):
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    validation_max_tokens: Optional[int] = None


@app.put("/admin/config/llm")
def admin_update_llm(body: LLMUpdate):
    """Update LLM parameters (TEMP: open during testing)."""
    config = {}
    if body.max_tokens is not None:
        config["max_tokens"] = body.max_tokens
    if body.temperature is not None:
        config["temperature"] = body.temperature
    if body.validation_max_tokens is not None:
        config["validation_max_tokens"] = body.validation_max_tokens
    return set_llm_config(config)


@app.get("/admin/metrics")
def admin_get_metrics():
    """Get full metrics including totals and per-tenant breakdown (TEMP: open during testing)."""
    return get_metrics()


@app.get("/admin/metrics/accounts")
def admin_list_accounts():
    """List tenant IDs that have metrics (TEMP: open during testing)."""
    return {"tenant_ids": get_all_tenant_ids()}


@app.get("/admin/metrics/account/{tenant_id}")
def admin_get_account_metrics(tenant_id: str):
    """Get metrics for a specific account/tenant (TEMP: open during testing)."""
    return get_metrics_by_tenant(tenant_id)


@app.get("/admin/logs")
def admin_get_logs(
    limit: int = 200,
    level: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """Get application logs, optionally filtered by tenant (TEMP: open during testing)."""
    limit = min(limit, 500)
    logs = get_logs(limit=limit, level=level, tenant_id=tenant_id)
    return {"logs": logs, "count": len(logs)}


# ============================================
# Main Query Endpoint (batch)
# ============================================

@app.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Convert natural language query to SQL and optionally execute it.
    """
    # Determine tenant_id from request body, header, or env (NO literal "default" fallback)
    tenant_id = request.tenant_id or x_tenant_id or settings.default_tenant_id
    
    # Track metrics: increment request count (track ALL requests, even failed ones)
    increment_request_count(tenant_id)
    
    if not tenant_id:
        increment_error_count("missing_tenant_id", tenant_id)
        raise HTTPException(
            status_code=400,
            detail="Missing tenant_id (accountId). Provide it in request body, X-Tenant-ID header, or set DEFAULT_TENANT_ID in .env"
        )
    
    # Reject literal "default" string
    if tenant_id == "default":
        increment_error_count("invalid_tenant_id", tenant_id)
        raise HTTPException(
            status_code=400,
            detail="Invalid tenant_id: 'default' is not allowed. Provide a valid tenant ID."
        )

    # Generate unique request_id and log incoming request
    request_id = log_request_start(logger, request.query, tenant_id)

    try:
        # Get schema context
        schema_context_str = schema_context.get_schema_context()

        # Generate response using Bedrock
        logger.info("Calling Bedrock to generate response...")
        bedrock_result = bedrock_client.generate_sql(
            natural_language_query=request.query,
            schema_context=schema_context_str,
            tenant_id=tenant_id,
            request_id=request_id
        )

        # Extract response components
        mode = bedrock_result.get("mode", "sql")
        response_text = bedrock_result.get("response")
        generated_sql = bedrock_result.get("sql")
        explanation = bedrock_result.get(
            "explanation",
            "Generated response from natural language."
        )

        # Handle non-SQL modes (chat or clarification)
        if mode in ("chat", "clarification"):
            logger.info(f"Bedrock returned {mode} mode - skipping SQL validation and execution")
            
            if mode == "chat":
                increment_chat_count(tenant_id)
            elif mode == "clarification":
                increment_clarification_count(tenant_id)
            
            log_request_end(logger, request_id, success=True)
            return AskResponse(
                sql="",
                explanation=explanation or response_text or "Chat response",
                natural_language_query=request.query,
                tenant_id=tenant_id,
                validated=False,
                rows=None,
                row_count=None,
                execution_error=None
            )

        # Only proceed with SQL validation/execution when mode == "sql"
        if mode != "sql":
            logger.warning(f"Unexpected mode '{mode}' - treating as non-SQL")
            log_request_end(logger, request_id, success=True)
            return AskResponse(
                sql="",
                explanation=explanation or "Unexpected response mode",
                natural_language_query=request.query,
                tenant_id=tenant_id,
                validated=False,
                rows=None,
                row_count=None,
                execution_error=None
            )

        # Mode is "sql" - validate that SQL was generated
        if not generated_sql:
            logger.error("Mode is 'sql' but no SQL was generated")
            increment_error_count("no_sql_generated", tenant_id)
            log_request_end(logger, request_id, success=False, error="No SQL generated in SQL mode")
            raise HTTPException(
                status_code=500,
                detail="Bedrock returned SQL mode but no SQL query was generated"
            )
        
        # Track metrics: SQL query generated
        increment_sql_query_count(tenant_id)

        # Log generated SQL
        safe_log_sql(logger, logging.INFO, "Generated SQL:", generated_sql)

        # Initialize guardrails only for SQL mode
        guardrails = SQLGuardrails(tenant_id)

        # Validate SQL
        is_valid, error_message = guardrails.validate_query(generated_sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {error_message}")
            increment_error_count("sql_validation_failed", tenant_id)
            log_request_end(logger, request_id, success=False, error=f"SQL validation failed: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"SQL validation failed: {error_message}"
            )
        
        logger.info("SQL validation passed")

        # Base response for SQL mode
        response_data = {
            "sql": generated_sql,
            "explanation": explanation,
            "natural_language_query": request.query,
            "tenant_id": tenant_id,
            "validated": True,
            "rows": None,
            "row_count": None,
            "execution_error": None,
            "validation_status": None,
            "validation_reasoning": None,
        }

        # Execute query if requested (only for SQL mode)
        if request.execute:
            logger.info("Executing SQL query...")
            try:
                start_time = time.time()
                rows = execute_query(generated_sql, request_id=request_id)
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Track metrics: record execution time
                record_query_execution_time(execution_time_ms)
                
                # Filter out cloudUUID from results for cleaner output
                rows = _filter_cloud_uuids(rows)
                
                response_data["rows"] = rows
                response_data["row_count"] = len(rows)
                logger.info(f"Query executed successfully | rows_returned={len(rows)}")
                
                # Data validation through prompting
                if rows and len(rows) > 0:
                    try:
                        validation = bedrock_client.validate_results(
                            original_query=request.query,
                            generated_sql=generated_sql,
                            results=rows[:20],  # Send first 20 rows for validation
                            tenant_id=tenant_id,
                        )
                        response_data["validation_status"] = validation.get("status", "unknown")
                        response_data["validation_reasoning"] = validation.get("reasoning", "")
                        logger.info(f"Data validation: {validation.get('status', 'unknown')}")
                    except Exception as val_err:
                        logger.warning(f"Data validation failed (non-critical): {val_err}")
                        response_data["validation_status"] = "skipped"
                        response_data["validation_reasoning"] = "Validation could not be performed"
                        
            except DatabaseExecutionError as db_exc:
                error_msg = str(db_exc)
                logger.error(f"Database execution error: {error_msg}")
                increment_error_count("database_execution_error", tenant_id)
                response_data["execution_error"] = error_msg

        # Log: Request completed successfully
        log_request_end(logger, request_id, success=True)
        return AskResponse(**response_data)

    except ClientError as aws_exc:
        error_code = aws_exc.response["Error"]["Code"]
        error_message = aws_exc.response["Error"]["Message"]
        logger.error(f"Bedrock API error ({error_code}): {error_message}")
        increment_error_count("bedrock_api_error", tenant_id)
        log_request_end(logger, request_id, success=False, error=f"Bedrock API error: {error_code}")
        raise HTTPException(
            status_code=503,
            detail=f"AWS Bedrock error ({error_code})"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Unexpected error processing query: {e}")
        increment_error_count("unexpected_error", tenant_id)
        log_request_end(logger, request_id, success=False, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ============================================
# Streaming Query Endpoint (SSE)
# ============================================

@app.post("/ask/stream")
async def ask_stream(
    request: AskRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Convert natural language query to SQL and execute it with Server-Sent Events streaming.
    
    SSE Events:
    - thinking: Model's reasoning / progress updates
    - sql: The generated SQL query
    - data_row: Individual row of results (streamed one by one)
    - validation: Data validation result
    - done: Final completion event
    - error: Error event
    """
    tenant_id = request.tenant_id or x_tenant_id or settings.default_tenant_id
    increment_request_count(tenant_id)
    
    if not tenant_id:
        increment_error_count("missing_tenant_id", tenant_id)
        raise HTTPException(
            status_code=400,
            detail="Missing tenant_id"
        )
    
    if tenant_id == "default":
        increment_error_count("invalid_tenant_id", tenant_id)
        raise HTTPException(
            status_code=400,
            detail="Invalid tenant_id: 'default' is not allowed."
        )

    request_id = log_request_start(logger, request.query, tenant_id)

    async def event_stream():
        """Generator that yields SSE events."""
        try:
            schema_context_str = schema_context.get_schema_context()
            yield _sse_event("thinking", {"message": "Analyzing your question..."})

            # Phase 2: Generate SQL using streaming Bedrock thinking
            bedrock_result = None
            for event in bedrock_client.generate_sql_stream(
                natural_language_query=request.query,
                schema_context=schema_context_str,
                tenant_id=tenant_id,
                request_id=request_id,
            ):
                if event.get("event") == "thinking":
                    yield _sse_event("thinking", {"message": event.get("text", "")})
                elif event.get("event") == "final":
                    bedrock_result = event.get("result")

            if bedrock_result is None:
                increment_error_count("bedrock_streaming_error", tenant_id)
                yield _sse_event("error", {"message": "Model did not return a valid response"})
                return

            mode = bedrock_result.get("mode", "sql")
            response_text = bedrock_result.get("response")
            generated_sql = bedrock_result.get("sql")
            explanation = bedrock_result.get("explanation", "Generated response from natural language.")

            # Handle non-SQL modes
            if mode in ("chat", "clarification"):
                if mode == "chat":
                    increment_chat_count(tenant_id)
                elif mode == "clarification":
                    increment_clarification_count(tenant_id)
                
                yield _sse_event("done", {
                    "mode": mode,
                    "message": explanation or response_text or "Chat response",
                    "sql": "",
                    "row_count": 0,
                })
                log_request_end(logger, request_id, success=True)
                return

            if mode != "sql" or not generated_sql:
                yield _sse_event("error", {"message": "Could not generate SQL for this question"})
                return

            increment_sql_query_count(tenant_id)

            # Validate SQL
            guardrails = SQLGuardrails(tenant_id)
            is_valid, error_message = guardrails.validate_query(generated_sql)
            
            if not is_valid:
                increment_error_count("sql_validation_failed", tenant_id)
                yield _sse_event("error", {"message": f"SQL validation failed: {error_message}"})
                return

            # Send the SQL
            yield _sse_event("sql", {
                "sql": generated_sql,
                "explanation": explanation,
            })

            # Phase 3: Execute and stream data
            if request.execute:
                yield _sse_event("thinking", {"message": "Executing query against the database..."})
                
                try:
                    start_time = time.time()
                    rows = execute_query(generated_sql, request_id=request_id)
                    execution_time_ms = (time.time() - start_time) * 1000
                    record_query_execution_time(execution_time_ms)
                    
                    # Filter out cloudUUID from results
                    rows = _filter_cloud_uuids(rows)
                    
                    # Get column headers from first row
                    if rows and len(rows) > 0:
                        columns = list(rows[0].keys())
                        yield _sse_event("columns", {"columns": columns})
                        
                        # Stream rows one by one for dynamic effect
                        for i, row in enumerate(rows):
                            yield _sse_event("data_row", {"row": row, "index": i})
                    
                    yield _sse_event("thinking", {
                        "message": f"Query returned {len(rows)} result{'s' if len(rows) != 1 else ''}."
                    })
                    
                    # Phase 4: Data validation
                    if rows and len(rows) > 0:
                        yield _sse_event("thinking", {"message": "Validating results match your question..."})
                        try:
                            validation = bedrock_client.validate_results(
                                original_query=request.query,
                                generated_sql=generated_sql,
                                results=rows[:20],
                                tenant_id=tenant_id,
                            )
                            yield _sse_event("validation", {
                                "status": validation.get("status", "unknown"),
                                "reasoning": validation.get("reasoning", ""),
                            })
                        except Exception as val_err:
                            logger.warning(f"Streaming validation failed: {val_err}")
                            yield _sse_event("validation", {
                                "status": "skipped",
                                "reasoning": "Validation could not be performed",
                            })
                    
                    # Done
                    yield _sse_event("done", {
                        "mode": "sql",
                        "sql": generated_sql,
                        "row_count": len(rows),
                        "execution_time_ms": execution_time_ms,
                    })
                    
                except DatabaseExecutionError as db_exc:
                    yield _sse_event("error", {"message": f"Database error: {str(db_exc)}"})
            else:
                yield _sse_event("done", {
                    "mode": "sql",
                    "sql": generated_sql,
                    "row_count": 0,
                })
            
            log_request_end(logger, request_id, success=True)

        except ClientError as aws_exc:
            error_code = aws_exc.response["Error"]["Code"]
            error_message_str = aws_exc.response["Error"]["Message"]
            logger.error(f"Bedrock API error ({error_code}): {error_message_str}")
            increment_error_count("bedrock_api_error", tenant_id)
            yield _sse_event("error", {"message": f"AWS Bedrock error: {error_code}"})

        except Exception as e:
            logger.exception(f"Streaming error: {e}")
            increment_error_count("unexpected_error", tenant_id)
            yield _sse_event("error", {"message": "Internal server error"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================
# Helper Functions
# ============================================

def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def _filter_cloud_uuids(rows: List[dict]) -> List[dict]:
    """
    Remove UUID-style and internal identifier columns from query results to
    avoid confusing clients or exposing low-level identifiers.

    Any column whose name contains 'uuid' (case-insensitive), and accountId,
    are stripped from the visible results. The model can still use these
    fields internally in SQL for joins and filters.
    """
    if not rows:
        return rows
    
    filtered = []
    for row in rows:
        new_row = {}
        for key, value in row.items():
            key_lower = key.lower()
            # Skip any UUID-style identifiers and internal tenant identifiers
            if "uuid" in key_lower:
                continue
            if key_lower == "accountid":
                continue
            new_row[key] = value
        filtered.append(new_row)
    
    return filtered
