import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

from app.bedrock.client import BedrockClient
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
    explanation: str
    natural_language_query: str
    tenant_id: str
    validated: bool
    rows: Optional[list] = None
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
    
    - **query**: Natural language question
    - **tenant_id**: Tenant ID (can also be provided via X-Tenant-ID header)
    - **execute**: If true, execute the generated SQL and return results
    """
    # Determine tenant_id
    tenant_id = request.tenant_id or x_tenant_id or os.getenv("DEFAULT_TENANT_ID", "default")
    
    logger.info(f"Processing query for tenant {tenant_id}: {request.query[:100]}...")
    
    try:
        # Get schema context
        schema_context_str = schema_context.get_schema_context()
        
        # Generate SQL using Bedrock
        logger.info("Calling Bedrock to generate SQL...")
        bedrock_result = bedrock_client.generate_sql(
            natural_language_query=request.query,
            schema_context=schema_context_str,
            tenant_id=tenant_id
        )
        
        generated_sql = bedrock_result["sql"]
        explanation = bedrock_result.get("explanation", "Generated SQL query from natural language.")
        
        logger.info(f"Generated SQL: {generated_sql[:200]}...")
        
        # Validate SQL with guardrails
        guardrails = SQLGuardrails(tenant_id)
        is_valid, error_message = guardrails.validate_query(generated_sql)
        
        if not is_valid:
            logger.warning(f"SQL validation failed: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"SQL validation failed: {error_message}"
            )
        
        logger.info("SQL validation passed")
        
        # Prepare response
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
        
        # Execute query if requested
        if request.execute:
            logger.info("Executing SQL query...")
            try:
                rows = execute_query(generated_sql)
                response_data["rows"] = rows
                response_data["row_count"] = len(rows)
                logger.info(f"Query executed successfully, returned {len(rows)} rows")
            except DatabaseExecutionError as db_exc:
                error_msg = str(db_exc)
                logger.error(f"Database execution error: {error_msg}")
                response_data["execution_error"] = error_msg
                # Don't fail the request, just include the error in response
        
        return AskResponse(**response_data)
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Bedrock API error ({error_code}): {error_message}")
        raise HTTPException(
            status_code=503,
            detail=f"AWS Bedrock service error ({error_code}): {error_message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
