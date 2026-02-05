import logging
<<<<<<< HEAD
from typing import Optional, List, Any
from sqlalchemy.orm import Session

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
=======
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Any

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

from app.bedrock.client import BedrockClient
from app.config import settings
from app.executor.executor import execute_query, DatabaseExecutionError
from app.logging.logger import (
    get_logger,
    log_request_start,
    log_request_end,
<<<<<<< HEAD
    safe_log_sql,
=======
    set_request_context,
    safe_log_sql,
    safe_truncate,
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
)
from app.logging import get_logs
from app.metrics import (
    get_metrics,
    increment_request_count,
    increment_error_count,
    increment_sql_query_count,
    increment_chat_count,
    increment_clarification_count,
    record_query_execution_time,
<<<<<<< HEAD
=======
    record_bedrock_call_time,
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
)
from app.safety.guardrails import SQLGuardrails
from app.schema.context import SchemaContext

<<<<<<< HEAD
# OAuth and authentication
from app.database import init_db, get_db
from app.auth import get_current_user, require_admin
from app.oauth import verify_google_token, get_or_create_user
from app.models import User

=======
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
# Get structured logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title="Sargon Partners AI Chatbot API",
    description="Natural language to SQL query API powered by AWS Bedrock",
    version="1.0.0"
)

<<<<<<< HEAD
# Configure CORS - allow frontend URL from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ],
=======
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Vite default ports
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
bedrock_client = BedrockClient()
schema_context = SchemaContext()

<<<<<<< HEAD
# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        init_db()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Request/Response models for OAuth
class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth token."""
    token: str = Field(..., description="Google ID token from frontend")

class AuthResponse(BaseModel):
    """Response model for successful authentication."""
    access_token: str
    token_type: str = "bearer"
    user: dict
=======
# Simple token storage (in production, use Redis or database)
_active_tokens: dict[str, datetime] = {}
TOKEN_EXPIRY_HOURS = 24

# Security
security = HTTPBearer(auto_error=False)

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    expires_at: str
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9

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
<<<<<<< HEAD
            "/auth/google": "POST - Authenticate with Google OAuth",
            "/auth/me": "GET - Get current user info",
            "/auth/logout": "POST - Logout",
            "/ask": "POST - Convert natural language to SQL",
            "/health": "GET - Health check",
            "/db-ping": "GET - Database connection test",
            "/logs": "GET - View application logs (auth required)",
            "/analytics": "GET - Get analytics and metrics (auth required)"
        }
    }

# ============================================
# Authentication Endpoints
# ============================================

@app.post("/auth/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth token.
    
    The frontend sends the Google ID token obtained from Google Sign-In.
    We verify it with Google, create/update the user, and return our JWT token.
    """
    # Verify Google token
    google_user_info = await verify_google_token(request.token)
    
    if not google_user_info:
        logger.warning("Invalid Google token provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid Google token"
        )
    
    # Get or create user
    try:
        user = get_or_create_user(db, google_user_info)
    except Exception as e:
        logger.error(f"Failed to get/create user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user session"
        )
    
    # Generate JWT token
    from app.auth import create_access_token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user.to_dict()
    )

@app.get("/auth/me")
def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    return {"user": user.to_dict()}

@app.post("/auth/logout")
def logout(user: User = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: With JWT tokens, logout is primarily handled client-side by removing the token.
    This endpoint is provided for logging purposes and future session management.
    """
    logger.info(f"User logged out: {user.email}")
    return {"message": "Logged out successfully"}

@app.get("/auth/verify")
def verify_auth(user: User = Depends(get_current_user)):
    """Verify if current token is valid and return user info."""
    return {"authenticated": True, "user": user.to_dict()}
=======
            "/ask": "POST - Convert natural language to SQL",
            "/health": "GET - Health check",
            "/db-ping": "GET - Database connection test",
            "/logs": "GET - View application logs",
            "/analytics": "GET - Get analytics and metrics"
        }
    }

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Verify authentication token."""
    if not credentials:
        return False
    
    token = credentials.credentials
    if token not in _active_tokens:
        return False
    
    # Check if token expired
    if datetime.now() > _active_tokens[token]:
        del _active_tokens[token]
        return False
    
    return True

def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Dependency to require authentication."""
    if not verify_token(credentials):
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid or expired token")
    return True

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Simple username/password login.
    
    Returns a token that should be included in Authorization header for protected endpoints.
    """
    # Verify credentials
    if request.username != settings.auth_username or request.password != settings.auth_password:
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    _active_tokens[token] = expires_at
    
    logger.info(f"User '{request.username}' logged in successfully")
    
    return LoginResponse(
        token=token,
        expires_at=expires_at.isoformat()
    )

@app.post("/logout")
def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Logout and invalidate token."""
    if credentials and credentials.credentials in _active_tokens:
        del _active_tokens[credentials.credentials]
        logger.info("User logged out")
    return {"message": "Logged out successfully"}

@app.get("/auth/verify")
def verify_auth(authenticated: bool = Depends(require_auth)):
    """Verify if current token is valid."""
    return {"authenticated": True}
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9

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

@app.get("/logs")
def get_application_logs(
    limit: int = 100,
    level: Optional[str] = None,
<<<<<<< HEAD
    user: User = Depends(get_current_user)
=======
    authenticated: bool = Depends(require_auth)
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
):
    """
    Get recent application logs for viewing in the web interface.
    
    Args:
        limit: Maximum number of logs to return (default: 100, max: 500)
        level: Filter by log level (INFO, WARNING, ERROR, DEBUG) - optional
        
    Returns:
        List of log entries with timestamp, level, module, request_id, tenant_id, and message
    """
    # Limit max logs to prevent memory issues
    limit = min(limit, 500)
    
    logs = get_logs(limit=limit, level=level)
    
    return {
        "logs": logs,
        "count": len(logs),
        "total_available": len(logs),
    }

@app.get("/analytics")
<<<<<<< HEAD
def get_analytics(user: User = Depends(get_current_user)):
=======
def get_analytics(authenticated: bool = Depends(require_auth)):
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
    """
    Get analytics and metrics data for the dashboard.
    
    Returns:
        Dictionary with metrics including:
        - Summary (total requests, errors, SQL queries, etc.)
        - Error breakdown by type
        - Performance metrics (avg execution times)
        - Hourly request/error trends
    """
    return get_metrics()

@app.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Convert natural language query to SQL and optionally execute it.
    """
    # Track metrics: increment request count (track ALL requests, even failed ones)
    increment_request_count()
    
    # Determine tenant_id from request body, header, or env (NO literal "default" fallback)
    tenant_id = request.tenant_id or x_tenant_id or settings.default_tenant_id
    
    if not tenant_id:
        increment_error_count("missing_tenant_id")
        raise HTTPException(
            status_code=400,
            detail="Missing tenant_id (accountId). Provide it in request body, X-Tenant-ID header, or set DEFAULT_TENANT_ID in .env"
        )
    
    # Reject literal "default" string
    if tenant_id == "default":
        increment_error_count("invalid_tenant_id")
        raise HTTPException(
            status_code=400,
            detail="Invalid tenant_id: 'default' is not allowed. Provide a valid tenant ID."
        )

    # Generate unique request_id and log incoming request
    # This creates a request-scoped logging context for all subsequent logs
    request_id = log_request_start(logger, request.query, tenant_id)

    try:
        # Get schema context
        schema_context_str = schema_context.get_schema_context()

        # Generate response using Bedrock
        # Log: Track when we call Bedrock API
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
            # Log: Track when we skip SQL processing for chat/clarification
            logger.info(f"Bedrock returned {mode} mode - skipping SQL validation and execution")
            
            # Track metrics: increment chat/clarification count
            if mode == "chat":
                increment_chat_count()
            elif mode == "clarification":
                increment_clarification_count()
            
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
            # Log: Warning for unexpected modes
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
            # Log: Error when SQL mode but no SQL generated
            logger.error("Mode is 'sql' but no SQL was generated")
            increment_error_count("no_sql_generated")
            log_request_end(logger, request_id, success=False, error="No SQL generated in SQL mode")
            raise HTTPException(
                status_code=500,
                detail="Bedrock returned SQL mode but no SQL query was generated"
            )
        
        # Track metrics: SQL query generated (only when we have valid SQL)
        if generated_sql:
            increment_sql_query_count()

        # Log: Generated SQL (truncated for safety)
        # This helps debug what SQL was generated before validation
        safe_log_sql(logger, logging.INFO, "Generated SQL:", generated_sql)

        # Initialize guardrails only for SQL mode
        guardrails = SQLGuardrails(tenant_id)

        # Validate SQL
        # Log: Track SQL validation result (WARNING level for failures)
        is_valid, error_message = guardrails.validate_query(generated_sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {error_message}")
            increment_error_count("sql_validation_failed")
            log_request_end(logger, request_id, success=False, error=f"SQL validation failed: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"SQL validation failed: {error_message}"
            )
        
        # Log: SQL validation passed
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
            "execution_error": None
        }

        # Execute query if requested (only for SQL mode)
        if request.execute:
            # Log: Track when we execute SQL
            logger.info("Executing SQL query...")
            try:
                import time
                start_time = time.time()
                rows = execute_query(generated_sql, request_id=request_id)
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Track metrics: record execution time
                record_query_execution_time(execution_time_ms)
                
                response_data["rows"] = rows
                response_data["row_count"] = len(rows)
                # Log: Track number of rows returned (helps debug query results)
                logger.info(f"Query executed successfully | rows_returned={len(rows)}")
            except DatabaseExecutionError as db_exc:
                # Log: Execution errors without crashing (ERROR level)
                error_msg = str(db_exc)
                logger.error(f"Database execution error: {error_msg}")
                increment_error_count("database_execution_error")
                response_data["execution_error"] = error_msg

        # Log: Request completed successfully
        log_request_end(logger, request_id, success=True)
        return AskResponse(**response_data)

    except ClientError as aws_exc:
        error_code = aws_exc.response["Error"]["Code"]
        error_message = aws_exc.response["Error"]["Message"]
        logger.error(f"Bedrock API error ({error_code}): {error_message}")
        increment_error_count("bedrock_api_error")
        log_request_end(logger, request_id, success=False, error=f"Bedrock API error: {error_code}")
        raise HTTPException(
            status_code=503,
            detail=f"AWS Bedrock error ({error_code})"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Unexpected error processing query: {e}")
        increment_error_count("unexpected_error")
        log_request_end(logger, request_id, success=False, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
