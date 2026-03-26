"""
Conversation history persistence.

Stores each completed query/response pair in a `conversations` table so users
see their history across devices and sessions. All queries are scoped to
(tenant_id, user_sub) so tenants never see each other's data.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.executor.executor import engine
from app.logging.logger import get_logger

logger = get_logger(__name__)


def init_conversations_table() -> None:
    """Create the conversations table if it doesn't already exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          VARCHAR(36)  NOT NULL PRIMARY KEY,
                tenant_id   VARCHAR(64)  NOT NULL,
                user_sub    VARCHAR(255) NOT NULL,
                query       TEXT         NOT NULL,
                mode        VARCHAR(20),
                response    TEXT,
                sql_generated TEXT,
                row_count   INT          NOT NULL DEFAULT 0,
                created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tenant_user_time (tenant_id, user_sub, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        conn.commit()
    logger.info("conversations table ready")


def save_conversation(
    *,
    tenant_id: str,
    user_sub: str,
    query: str,
    mode: Optional[str] = None,
    response: Optional[str] = None,
    sql_generated: Optional[str] = None,
    row_count: int = 0,
) -> str:
    """Persist one conversation turn. Returns the new conversation ID."""
    conv_id = str(uuid.uuid4())
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO conversations
                    (id, tenant_id, user_sub, query, mode, response, sql_generated, row_count, created_at)
                VALUES
                    (:id, :tenant_id, :user_sub, :query, :mode, :response, :sql_generated, :row_count, :created_at)
            """),
            {
                "id": conv_id,
                "tenant_id": tenant_id,
                "user_sub": user_sub,
                "query": query,
                "mode": mode,
                "response": response,
                "sql_generated": sql_generated,
                "row_count": row_count,
                "created_at": datetime.utcnow(),
            },
        )
        conn.commit()
    return conv_id


def get_conversations(
    tenant_id: str,
    user_sub: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Return the most recent `limit` conversations for this user+tenant,
    ordered oldest-first so the frontend can render them top-to-bottom.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, tenant_id, user_sub, query, mode, response,
                       sql_generated, row_count, created_at
                FROM conversations
                WHERE tenant_id = :tenant_id AND user_sub = :user_sub
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"tenant_id": tenant_id, "user_sub": user_sub, "limit": limit},
        )
        rows = result.fetchall()

    # Reverse so oldest is first (chronological display order)
    items = list(reversed([dict(r._mapping) for r in rows]))
    # Serialise datetime to ISO string for JSON
    for item in items:
        if isinstance(item.get("created_at"), datetime):
            item["created_at"] = item["created_at"].isoformat()
    return items
