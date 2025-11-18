"""FastAPI server for NL→SQL query generation using AWS Bedrock."""

import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.bedrock import BedrockClient
from app.safety import SQLGuardrails
from app.schema import SchemaContext


# Initialize FastAPI app
app = FastAPI(
    title="NL→SQL API",
    description="Natural language to SQL query generation using AWS Bedrock with tenant isolation",
    version="1.0.0",
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
bedrock_client = BedrockClient()
schema_context = SchemaContext()


# Request/Response models
class AskRequest(BaseModel):
    """Request model for /ask endpoint."""

    query: str = Field(..., description="Natural language query", min_length=1)
    tenant_id: Optional[str] = Field(None, description="Tenant ID for isolation")


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""

    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the generated SQL")
    natural_language_query: str = Field(..., description="Original natural language query")
    tenant_id: str = Field(..., description="Tenant ID used for isolation")
    validated: bool = Field(..., description="Whether SQL passed safety validation")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "message": "NL→SQL API with AWS Bedrock",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    """
    Convert natural language query to SQL using AWS Bedrock.

    Args:
        request: AskRequest with natural language query and optional tenant_id
        x_tenant_id: Tenant ID from header (alternative to request body)

    Returns:
        AskResponse with generated SQL, explanation, and validation status

    Raises:
        HTTPException: If query generation fails or SQL is unsafe
    """
    # Get tenant ID from request body or header
    tenant_id = request.tenant_id or x_tenant_id or os.getenv("DEFAULT_TENANT_ID", "default")

    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant ID is required (provide in request body or X-Tenant-ID header)",
        )

    try:
        # Get schema context
        schema_context_str = schema_context.get_schema_context()

        # Generate SQL using Bedrock
        bedrock_response = bedrock_client.generate_sql(
            natural_language_query=request.query,
            schema_context=schema_context_str,
            tenant_id=tenant_id,
        )

        generated_sql = bedrock_response["sql"]
        explanation = bedrock_response.get("explanation", "Generated SQL query from natural language.")

        # Validate SQL with safety guardrails
        guardrails = SQLGuardrails(tenant_id=tenant_id)
        is_valid, error_message = guardrails.validate_query(generated_sql)

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Generated SQL failed safety validation: {error_message}",
            )

        # Return validated SQL
        return AskResponse(
            sql=generated_sql,
            explanation=explanation,
            natural_language_query=request.query,
            tenant_id=tenant_id,
            validated=True,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error in production
        error_msg = str(e)
        if "Bedrock API error" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=f"AWS Bedrock service error: {error_msg}",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {error_msg}",
        )
