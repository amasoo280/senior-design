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

# Default guardrails (match current SQLGuardrails)
DEFAULT_GUARDRAILS = {
    "allowed_tenant_ids": [
        "c55b3c70-7aa7-11eb-a7e8-9b4baf296adf",
        "eaeddcf1-fb98-11eb-94c9-b1e578657155",
    ],
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

# Prompt template uses placeholders: {schema_context}, {tenant_id}, {natural_language_query}
DEFAULT_PROMPT_TEMPLATE = None  # None = use built-in prompt in BedrockClient


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
        "allowed_tenant_ids": guardrails.get("allowed_tenant_ids") or DEFAULT_GUARDRAILS["allowed_tenant_ids"],
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
