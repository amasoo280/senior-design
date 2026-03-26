"""
Conversation history persistence.

Two tables:
- chat_sessions  — one row per conversation thread (title, timestamps)
- conversations  — one row per user+assistant turn, foreign-keyed to a session

All data is scoped to (tenant_id, user_sub) for multi-tenant isolation.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.executor.executor import engine
from app.logging.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Table initialisation
# ---------------------------------------------------------------------------

def init_conversations_table() -> None:
    """Create chat_sessions and conversations tables if they don't exist.
    Also adds session_id column to conversations if upgrading from an older schema."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id          VARCHAR(36)  NOT NULL PRIMARY KEY,
                tenant_id   VARCHAR(64)  NOT NULL,
                user_sub    VARCHAR(255) NOT NULL,
                title       VARCHAR(255) NOT NULL DEFAULT 'New Chat',
                created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_sessions_tenant_user_updated (tenant_id, user_sub, updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id            VARCHAR(36)  NOT NULL PRIMARY KEY,
                session_id    VARCHAR(36)  NOT NULL,
                tenant_id     VARCHAR(64)  NOT NULL,
                user_sub      VARCHAR(255) NOT NULL,
                query         TEXT         NOT NULL,
                mode          VARCHAR(20),
                response      TEXT,
                sql_generated TEXT,
                row_count     INT          NOT NULL DEFAULT 0,
                created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_conv_session (session_id),
                INDEX idx_conv_tenant_user (tenant_id, user_sub)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

        # Migration: add session_id column if upgrading from old schema (no-op if already present)
        try:
            conn.execute(text(
                "ALTER TABLE conversations ADD COLUMN session_id VARCHAR(36) NOT NULL DEFAULT '' AFTER id"
            ))
        except Exception:
            pass  # Column already exists

        conn.commit()
    logger.info("chat_sessions and conversations tables ready")


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def create_session(*, tenant_id: str, user_sub: str, title: str = "New Chat") -> str:
    """Create a new chat session and return its ID."""
    session_id = str(uuid.uuid4())
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_sessions (id, tenant_id, user_sub, title, created_at, updated_at)
                VALUES (:id, :tenant_id, :user_sub, :title, :now, :now)
            """),
            {"id": session_id, "tenant_id": tenant_id, "user_sub": user_sub,
             "title": title[:255], "now": datetime.utcnow()},
        )
        conn.commit()
    return session_id


def update_session_title(session_id: str, title: str) -> None:
    """Update a session's title (called after the first message is sent)."""
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE chat_sessions SET title = :title WHERE id = :id"),
            {"title": title[:255], "id": session_id},
        )
        conn.commit()


def touch_session(session_id: str) -> None:
    """Bump updated_at so the session floats to the top of the list."""
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE chat_sessions SET updated_at = :now WHERE id = :id"),
            {"now": datetime.utcnow(), "id": session_id},
        )
        conn.commit()


def get_sessions(tenant_id: str, user_sub: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return sessions for this user ordered newest-first."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT s.id, s.title, s.created_at, s.updated_at,
                       COUNT(c.id) AS message_count
                FROM chat_sessions s
                LEFT JOIN conversations c ON c.session_id = s.id
                WHERE s.tenant_id = :tenant_id AND s.user_sub = :user_sub
                GROUP BY s.id, s.title, s.created_at, s.updated_at
                ORDER BY s.updated_at DESC
                LIMIT :limit
            """),
            {"tenant_id": tenant_id, "user_sub": user_sub, "limit": limit},
        )
        rows = result.fetchall()

    items = [dict(r._mapping) for r in rows]
    for item in items:
        for key in ("created_at", "updated_at"):
            if isinstance(item.get(key), datetime):
                item[key] = item[key].isoformat()
    return items


def delete_session(session_id: str, tenant_id: str, user_sub: str) -> bool:
    """Delete a session and all its conversations. Returns True if a row was deleted."""
    with engine.connect() as conn:
        # Verify ownership before deleting
        row = conn.execute(
            text("SELECT id FROM chat_sessions WHERE id = :id AND tenant_id = :tid AND user_sub = :sub"),
            {"id": session_id, "tid": tenant_id, "sub": user_sub},
        ).fetchone()
        if not row:
            return False
        conn.execute(text("DELETE FROM conversations WHERE session_id = :id"), {"id": session_id})
        conn.execute(text("DELETE FROM chat_sessions WHERE id = :id"), {"id": session_id})
        conn.commit()
    return True


# ---------------------------------------------------------------------------
# Conversation helpers
# ---------------------------------------------------------------------------

def save_conversation(
    *,
    session_id: str,
    tenant_id: str,
    user_sub: str,
    query: str,
    mode: Optional[str] = None,
    response: Optional[str] = None,
    sql_generated: Optional[str] = None,
    row_count: int = 0,
) -> str:
    """Persist one conversation turn and bump the session's updated_at."""
    conv_id = str(uuid.uuid4())
    now = datetime.utcnow()
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO conversations
                    (id, session_id, tenant_id, user_sub, query, mode, response, sql_generated, row_count, created_at)
                VALUES
                    (:id, :session_id, :tenant_id, :user_sub, :query, :mode, :response, :sql_generated, :row_count, :created_at)
            """),
            {
                "id": conv_id, "session_id": session_id,
                "tenant_id": tenant_id, "user_sub": user_sub,
                "query": query, "mode": mode, "response": response,
                "sql_generated": sql_generated, "row_count": row_count,
                "created_at": now,
            },
        )
        conn.execute(
            text("UPDATE chat_sessions SET updated_at = :now WHERE id = :id"),
            {"now": now, "id": session_id},
        )
        conn.commit()
    return conv_id


def get_conversations(
    session_id: str,
    tenant_id: str,
    user_sub: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return all turns for a session, oldest-first."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT c.id, c.session_id, c.query, c.mode, c.response,
                       c.sql_generated, c.row_count, c.created_at
                FROM conversations c
                JOIN chat_sessions s ON s.id = c.session_id
                WHERE c.session_id = :session_id
                  AND s.tenant_id = :tenant_id
                  AND s.user_sub = :user_sub
                ORDER BY c.created_at ASC
                LIMIT :limit
            """),
            {"session_id": session_id, "tenant_id": tenant_id,
             "user_sub": user_sub, "limit": limit},
        )
        rows = result.fetchall()

    items = [dict(r._mapping) for r in rows]
    for item in items:
        if isinstance(item.get("created_at"), datetime):
            item["created_at"] = item["created_at"].isoformat()
    return items
