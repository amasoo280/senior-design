import logging
import os
from typing import Optional, List, Any

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

from app.bedrock.client import BedrockClient
from app.config import settings
from app.executor.executor import execute_query, DatabaseExecutionError
from app.safety.guardrails import SQLGuardrails
from app.schema.context import SchemaContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sargon Partners AI Chatbot API",
    description="Natural language to SQL query API powered by AWS Bedrock",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
bedrock_client = BedrockClient()
schema_context = SchemaContext()

# Request/Response models
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

@app.get("/")
def root():
    return {
        "name": "Sargon Partners AI Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/ask": "POST - Convert natural language to SQL",
            "/health": "GET - Health check",
            "/db-ping": "GET - Database connection test"
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
    
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Missing tenant_id (accountId). Provide it in request body, X-Tenant-ID header, or set DEFAULT_TENANT_ID in .env"
        )
    
    # Reject literal "default" string
    if tenant_id == "default":
        raise HTTPException(
            status_code=400,
            detail="Invalid tenant_id: 'default' is not allowed. Provide a valid tenant ID."
        )

    logger.info(f"Processing query for tenant {tenant_id}: {request.query[:100]}...")

    try:
        # Get schema context
        schema_context_str = schema_context.get_schema_context()

        # Generate response using Bedrock
        logger.info("Calling Bedrock to generate response...")
        bedrock_result = bedrock_client.generate_sql(
            natural_language_query=request.query,
            schema_context=schema_context_str,
            tenant_id=tenant_id
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
            raise HTTPException(
                status_code=500,
                detail="Bedrock returned SQL mode but no SQL query was generated"
            )

        logger.info(f"Generated SQL: {generated_sql[:200]}...")

        # Initialize guardrails only for SQL mode
        guardrails = SQLGuardrails(tenant_id)

        # Validate SQL
        is_valid, error_message = guardrails.validate_query(generated_sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"SQL validation failed: {error_message}"
            )

        # Base response for SQL mode
        response_data = {
            "sql": generated_sql,
            "explanation": explanation,
            "natural_language_query": request.query,
            "tenant_id": tenant_id,
            "validated": True,
            "rows": None,
            "row_count": None,
            "execution_error": None
        }

        # Execute query if requested (only for SQL mode)
        if request.execute:
            logger.info("Executing SQL query...")
            try:
                rows = execute_query(generated_sql)
                response_data["rows"] = rows
                response_data["row_count"] = len(rows)
            except DatabaseExecutionError as db_exc:
                error_msg = str(db_exc)
                logger.error(f"Database execution error: {error_msg}")
                response_data["execution_error"] = error_msg

        return AskResponse(**response_data)

    except ClientError as aws_exc:
        error_code = aws_exc.response["Error"]["Code"]
        error_message = aws_exc.response["Error"]["Message"]
        logger.error(f"Bedrock API error ({error_code}): {error_message}")
        raise HTTPException(
            status_code=503,
            detail=f"AWS Bedrock error ({error_code})"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Unexpected error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
