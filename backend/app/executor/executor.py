from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, List, Optional

from app.config import settings

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
)

class DatabaseExecutionError(Exception):
    pass

def execute_query(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    params = params or {}
    try:
        with engine.connect() as conn:
            result: Result = conn.execute(text(sql), params)
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
    except SQLAlchemyError as exc:
        raise DatabaseExecutionError(str(exc)) from exc
