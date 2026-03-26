import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result
from sqlalchemy.exc import SQLAlchemyError, TimeoutError as SQLTimeoutError
from typing import Any, Dict, List, Optional

from app.config import settings
from app.logging.logger import get_logger, set_request_context, safe_log_sql

logger = get_logger(__name__)

DATABASE_URL = (
    f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
    connect_args={
        "connect_timeout": settings.db_query_timeout_seconds,
    }
)

class DatabaseExecutionError(Exception):
    """Raised when database query execution fails."""
    pass

def execute_query(
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return results as a list of dictionaries.
    
    Args:
        sql: SQL query string (must be a SELECT query)
        params: Optional query parameters for parameterized queries
        request_id: Optional request ID for logging context
        
    Returns:
        List of dictionaries, where each dictionary represents a row
        
    Raises:
        DatabaseExecutionError: If query execution fails
    """
    # Set request context for logging if provided
    if request_id:
        set_request_context(request_id)
    
    params = params or {}
    
    # Log: SQL execution start (with timeout info)
    logger.info(f"Executing SQL query (timeout: {settings.db_query_timeout_seconds}s)")
    
    # Log: Final SQL to be executed (truncated for safety)
    # This helps debug what SQL is actually being executed
    safe_log_sql(logger, logging.INFO, "Final SQL to execute:", sql)
    
    try:
        with engine.connect() as conn:
            # Set statement timeout if supported
            try:
                conn.execute(text(f"SET SESSION max_execution_time = {settings.db_query_timeout_seconds * 1000}"))
            except Exception:
                # Some MySQL versions may not support this, continue anyway
                pass
            
            result: Result = conn.execute(text(sql), params)
            rows = result.fetchmany(settings.db_max_result_rows + 1)
            truncated = len(rows) > settings.db_max_result_rows
            if truncated:
                rows = rows[:settings.db_max_result_rows]
            row_count = len(rows)

            if truncated:
                logger.warning(
                    f"Query result truncated to {settings.db_max_result_rows} rows (limit: DB_MAX_RESULT_ROWS)"
                )

            # Log: Number of rows returned (helps debug query results)
            logger.info(f"Query executed successfully | rows_returned={row_count} | truncated={truncated}")

            return [dict(row._mapping) for row in rows]
    except SQLTimeoutError as exc:
        # Log: Query timeout errors (ERROR level)
        error_msg = f"Query timeout after {settings.db_query_timeout_seconds} seconds"
        logger.error(error_msg)
        raise DatabaseExecutionError(error_msg) from exc
    except SQLAlchemyError as exc:
        # Log: Database errors (ERROR level) - execution errors without crashing request
        error_msg = str(exc)
        logger.error(f"Database error: {error_msg}")
        raise DatabaseExecutionError(error_msg) from exc
    except Exception as exc:
        # Log: Unexpected database errors (ERROR level with stack trace)
        error_msg = f"Unexpected database error: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        raise DatabaseExecutionError(error_msg) from exc
