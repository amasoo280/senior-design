"""
Admin-editable configuration: guardrails, LLM prompt template, and LLM parameters.
Stored in backend/data/admin_config.json so admins can change behavior without code edits.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from app.logging.logger import get_logger

logger = get_logger(__name__)

# Default path relative to backend root
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _BACKEND_ROOT / "data"
_CONFIG_PATH = _CONFIG_DIR / "admin_config.json"


def _default_allowed_tenant_ids() -> list[str]:
    """
    Read allowed tenant IDs from ALLOWED_TENANT_IDS env var.
    Always includes DEFAULT_TENANT_ID so local dev works without
    manually adding it to ALLOWED_TENANT_IDS.
    """
    from app.config import settings  # local import to avoid circular dependency
    ids = list(settings.allowed_tenant_ids or [])
    if settings.default_tenant_id and settings.default_tenant_id not in ids:
        ids.append(settings.default_tenant_id)
    return ids


# Default guardrails (match current SQLGuardrails)
DEFAULT_GUARDRAILS = {
    "allowed_tenant_ids": [],  # populated at runtime via _default_allowed_tenant_ids()
    "dangerous_keywords": [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "GRANT", "REVOKE",
    ],
    "sql_injection_patterns": [
        r"--",
        r"/\*.*?\*/",
        r";\s*\w+",
        r"\bUNION\b\s+\bSELECT\b",
        r"\bOR\b\s+1\s*=\s*1",
    ],
    "tenant_column": "accountId",
}

DEFAULT_LLM = {
    "max_tokens": 4096,
    "temperature": 0.1,
    "validation_max_tokens": 1024,
}

# Prompt template uses placeholders: {schema_context}, {tenant_id}, {natural_language_query}, {db_context}
DEFAULT_PROMPT_TEMPLATE = None  # None = use built-in prompt in BedrockClient

# Free-form enum / business notes for the LLM (admin-edited). Enforced max length on save/read.
DB_CONTEXT_MAX_CHARS = 12000

# Default sample questions shown on the chat welcome screen.
DEFAULT_SAMPLE_QUESTIONS = [
    "Show me all equipment",
    "How many assets are at each location?",
    "List employees and their devices",
    "Show recent equipment movements",
]


def _ensure_config_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _read_raw() -> dict:
    """Read config file; return empty dict if missing or invalid."""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read admin config: {e}")
        return {}


def _write_raw(data: dict) -> None:
    _ensure_config_dir()
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_guardrails_config() -> dict:
    """Return guardrails config (merged with defaults)."""
    raw = _read_raw()
    guardrails = raw.get("guardrails") or {}
    return {
        "allowed_tenant_ids": guardrails.get("allowed_tenant_ids") or _default_allowed_tenant_ids(),
        "dangerous_keywords": guardrails.get("dangerous_keywords") or DEFAULT_GUARDRAILS["dangerous_keywords"],
        "sql_injection_patterns": guardrails.get("sql_injection_patterns") or DEFAULT_GUARDRAILS["sql_injection_patterns"],
        "tenant_column": guardrails.get("tenant_column") or DEFAULT_GUARDRAILS["tenant_column"],
    }


def set_guardrails_config(config: dict) -> dict:
    """Update guardrails in config file. Returns current full guardrails config."""
    raw = _read_raw()
    raw["guardrails"] = {
        "allowed_tenant_ids": config.get("allowed_tenant_ids", get_guardrails_config()["allowed_tenant_ids"]),
        "dangerous_keywords": config.get("dangerous_keywords", get_guardrails_config()["dangerous_keywords"]),
        "sql_injection_patterns": config.get("sql_injection_patterns", get_guardrails_config()["sql_injection_patterns"]),
        "tenant_column": config.get("tenant_column", get_guardrails_config()["tenant_column"]),
    }
    _write_raw(raw)
    return get_guardrails_config()


def get_prompt_template() -> Optional[str]:
    """Return custom prompt template or None to use built-in."""
    raw = _read_raw()
    return raw.get("prompt_template")


def set_prompt_template(template: Optional[str]) -> Optional[str]:
    raw = _read_raw()
    raw["prompt_template"] = template
    _write_raw(raw)
    return get_prompt_template()


def get_sample_questions() -> list[str]:
    """Return the configured sample questions or sensible defaults."""
    raw = _read_raw()
    questions = raw.get("sample_questions")
    if not questions or not isinstance(questions, list):
        return DEFAULT_SAMPLE_QUESTIONS
    # Ensure all items are strings
    return [str(q) for q in questions if isinstance(q, str) and q.strip()]


def set_sample_questions(questions: list[str]) -> list[str]:
    """Persist sample questions for the chat welcome screen."""
    raw = _read_raw()
    # Store only non-empty strings
    cleaned = [str(q).strip() for q in questions if str(q).strip()]
    raw["sample_questions"] = cleaned or DEFAULT_SAMPLE_QUESTIONS
    _write_raw(raw)
    return get_sample_questions()


def get_db_context() -> Optional[str]:
    """
    Optional free-text context (enums, codes) injected into NL→SQL prompts.
    Returns None if unset or empty after trim.
    """
    raw = _read_raw()
    val = raw.get("db_context")
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if len(s) > DB_CONTEXT_MAX_CHARS:
        logger.warning(
            "db_context truncated from %d to %d characters",
            len(s),
            DB_CONTEXT_MAX_CHARS,
        )
        return s[:DB_CONTEXT_MAX_CHARS]
    return s


def set_db_context(value: Optional[str]) -> Optional[str]:
    """Persist db_context; pass None or empty string to clear."""
    raw = _read_raw()
    if value is None or not str(value).strip():
        raw.pop("db_context", None)
    else:
        s = str(value).strip()
        if len(s) > DB_CONTEXT_MAX_CHARS:
            logger.warning(
                "db_context truncated on save from %d to %d characters",
                len(s),
                DB_CONTEXT_MAX_CHARS,
            )
            s = s[:DB_CONTEXT_MAX_CHARS]
        raw["db_context"] = s
    _write_raw(raw)
    return get_db_context()


def get_llm_config() -> dict:
    """Return LLM config (merged with defaults)."""
    raw = _read_raw()
    llm = raw.get("llm") or {}
    return {
        "max_tokens": llm.get("max_tokens", DEFAULT_LLM["max_tokens"]),
        "temperature": llm.get("temperature", DEFAULT_LLM["temperature"]),
        "validation_max_tokens": llm.get("validation_max_tokens", DEFAULT_LLM["validation_max_tokens"]),
    }


def set_llm_config(config: dict) -> dict:
    raw = _read_raw()
    current = get_llm_config()
    raw["llm"] = {
        "max_tokens": config.get("max_tokens", current["max_tokens"]),
        "temperature": config.get("temperature", current["temperature"]),
        "validation_max_tokens": config.get("validation_max_tokens", current["validation_max_tokens"]),
    }
    _write_raw(raw)
    return get_llm_config()
