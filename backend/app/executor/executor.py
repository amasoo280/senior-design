import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result
from sqlalchemy.exc import SQLAlchemyError, TimeoutError as SQLTimeoutError
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

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

def execute_query(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return results as a list of dictionaries.
    
    Args:
        sql: SQL query string (must be a SELECT query)
        params: Optional query parameters for parameterized queries
        
    Returns:
        List of dictionaries, where each dictionary represents a row
        
    Raises:
        DatabaseExecutionError: If query execution fails
    """
    params = params or {}
    logger.info(f"Executing SQL query (timeout: {settings.db_query_timeout_seconds}s)")
    logger.debug(f"SQL: {sql[:200]}...")  # Log first 200 chars
    
    try:
        with engine.connect() as conn:
            # Set statement timeout if supported
            try:
                conn.execute(text(f"SET SESSION max_execution_time = {settings.db_query_timeout_seconds * 1000}"))
            except Exception:
                # Some MySQL versions may not support this, continue anyway
                pass
            
            result: Result = conn.execute(text(sql), params)
            rows = result.fetchall()
            row_count = len(rows)
            logger.info(f"Query executed successfully, returned {row_count} rows")
            return [dict(row._mapping) for row in rows]
    except SQLTimeoutError as exc:
        error_msg = f"Query timeout after {settings.db_query_timeout_seconds} seconds"
        logger.error(error_msg)
        raise DatabaseExecutionError(error_msg) from exc
    except SQLAlchemyError as exc:
        error_msg = str(exc)
        logger.error(f"Database error: {error_msg}")
        raise DatabaseExecutionError(error_msg) from exc
    except Exception as exc:
        error_msg = f"Unexpected database error: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        raise DatabaseExecutionError(error_msg) from exc
