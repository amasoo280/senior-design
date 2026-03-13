"""
Centralized structured logging for FastAPI NL→SQL backend.

Provides:
- Structured log format with request_id and tenant_id
- Safe logging (no secrets, truncated SQL)
- Request-scoped logging context
"""

import contextvars
import logging
import os
import uuid
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.config import settings

# Context variables for request-scoped logging
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "tenant_id", default=None
)

# Maximum SQL length to log (truncate longer SQL)
MAX_SQL_LOG_LENGTH = 300

# In-memory log storage (circular buffer, max 1000 entries)
LOG_BUFFER_SIZE = 1000
_log_buffer: deque = deque(maxlen=LOG_BUFFER_SIZE)

# Secrets to never log (case-insensitive)
SECRET_KEYWORDS = [
    "password",
    "secret",
    "token",
    "key",
    "credential",
    "aws_secret",
    "access_key",
]


class InMemoryLogHandler(logging.Handler):
    """Custom handler that stores logs in memory for web viewing."""
    
    def emit(self, record: logging.LogRecord) -> None:
        """Store log record in memory buffer."""
        try:
            # Get request context
            request_id = request_id_var.get() or "N/A"
            tenant_id = tenant_id_var.get() or "N/A"
            
            # Format log entry
            log_entry: Dict[str, Any] = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "module": record.name,
                "request_id": request_id,
                "tenant_id": tenant_id,
                "message": record.getMessage(),
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.format(record)
            
            # Add to buffer (thread-safe append)
            _log_buffer.append(log_entry)
        except Exception:
            # Don't let logging errors break the application
            pass


class StructuredFormatter(logging.Formatter):
    """Custom formatter that includes request_id and tenant_id in log output."""

    def format(self, record: logging.LogRecord) -> str:
        # Add request_id and tenant_id to log record
        record.request_id = request_id_var.get() or "N/A"
        record.tenant_id = tenant_id_var.get() or "N/A"
        
        return super().format(record)


def setup_logging() -> None:
    """
    Configure the root logger with structured formatting.
    
    Log level can be set via LOG_LEVEL environment variable.
    Defaults to INFO if not set.
    """
    # Try to get log level from settings first, then fall back to env var
    try:
        from app.config import settings
        log_level = getattr(settings, "log_level", os.getenv("LOG_LEVEL", "INFO")).upper()
    except Exception:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Set structured formatter
    formatter = StructuredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | "
            "request_id=%(request_id)s | tenant_id=%(tenant_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add in-memory handler for web viewing
    memory_handler = InMemoryLogHandler()
    memory_handler.setLevel(getattr(logging, log_level, logging.INFO))
    memory_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(memory_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance configured with structured logging
    """
    return logging.getLogger(name)


def set_request_context(request_id: str, tenant_id: Optional[str] = None) -> None:
    """
    Set request context variables for logging.
    
    Args:
        request_id: Unique request identifier
        tenant_id: Tenant ID for this request (optional)
    """
    request_id_var.set(request_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def safe_truncate(text: str, max_length: int = MAX_SQL_LOG_LENGTH) -> str:
    """
    Truncate text safely for logging.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "...[truncated]"


def contains_secrets(text: str) -> bool:
    """
    Check if text contains potential secrets (case-insensitive).
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains secret keywords
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SECRET_KEYWORDS)


def safe_log_sql(logger: logging.Logger, level: int, message: str, sql: str) -> None:
    """
    Safely log SQL query (truncate, check for secrets).
    
    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.DEBUG, etc.)
        message: Log message prefix
        sql: SQL query to log
    """
    if not sql:
        logger.log(level, f"{message} [empty SQL]")
        return
    
    # Check for secrets
    if contains_secrets(sql):
        logger.log(level, f"{message} [SQL contains secrets, not logged]")
        return
    
    # Truncate if needed
    safe_sql = safe_truncate(sql, MAX_SQL_LOG_LENGTH)
    logger.log(level, f"{message} {safe_sql}")


def log_request_start(
    logger: logging.Logger,
    query: str,
    tenant_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> str:
    """
    Log incoming request start.
    
    Args:
        logger: Logger instance
        query: Natural language query (will be truncated)
        tenant_id: Tenant ID
        request_id: Request ID (generated if not provided)
        
    Returns:
        Request ID used for this request
    """
    if not request_id:
        request_id = generate_request_id()
    
    set_request_context(request_id, tenant_id)
    
    # Truncate query for logging
    safe_query = safe_truncate(query, 100)
    logger.info(f"Incoming request | query='{safe_query}'")
    
    if tenant_id:
        logger.info(f"Resolved tenant_id: {tenant_id}")
    
    return request_id


def log_request_end(
    logger: logging.Logger,
    request_id: str,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Log request completion.
    
    Args:
        logger: Logger instance
        request_id: Request ID
        success: Whether request succeeded
        error: Error message if request failed
    """
    if success:
        logger.info(f"Request completed successfully")
    else:
        logger.error(f"Request failed | error={error or 'Unknown error'}")


def log_raw_model_output(logger: logging.Logger, raw_output: str) -> None:
    """
    Log raw model output (only at DEBUG level to avoid cluttering logs).
    
    Args:
        logger: Logger instance
        raw_output: Raw text output from Bedrock model
    """
    # Only log raw output at DEBUG level (controlled by LOG_LEVEL env var)
    safe_output = safe_truncate(raw_output, 500)  # Truncate to 500 chars for raw output
    logger.debug(f"Raw model output: {safe_output}")


def get_logs(
    limit: int = 100,
    level: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get recent logs from memory buffer.
    
    Args:
        limit: Maximum number of logs to return (default: 100)
        level: Filter by log level (e.g., "INFO", "ERROR") - optional
        tenant_id: Filter by tenant/account ID - optional
        
    Returns:
        List of log entries (most recent first)
    """
    logs = list(_log_buffer)
    
    if level:
        logs = [log for log in logs if log["level"] == level.upper()]
    if tenant_id:
        logs = [log for log in logs if log.get("tenant_id") == tenant_id]
    
    return logs[-limit:][::-1]


# Initialize logging on module import
setup_logging()

