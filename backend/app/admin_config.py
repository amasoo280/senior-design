"""
Admin-configurable guardrails and prompt template.

Loaded from a JSON file; falls back to defaults if file is missing.
Refreshed only when admin saves (no per-query file read).
"""

import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

# Default guardrails (match original guardrails.py)
DEFAULT_ALLOWED_TENANT_IDS = [
    "c55b3c70-7aa7-11eb-a7e8-9b4baf296adf",
    "eaeddcf1-fb98-11eb-94c9-b1e578657155",
]
DEFAULT_DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "GRANT", "REVOKE",
]
DEFAULT_SQL_INJECTION_PATTERNS = [
    r"--",
    r"/\*.*?\*/",
    r";\s*\w+",
    r"\bUNION\b\s+\bSELECT\b",
    r"\bOR\b\s+1\s*=\s*1",
]
DEFAULT_TENANT_COLUMN = "accountId"

DEFAULT_PROMPT_TEMPLATE = """You are an AI assistant for an asset-tracking system.

Decide how to respond to the user's message.

Choose ONE mode:
- chat: greetings or general questions
- clarification: request is ambiguous or missing details
- sql: request clearly asks for data

When responding:
- Be helpful and concise.
- Use natural language.

CRITICAL OUTPUT RULES:
- The response MUST be valid JSON.
- Do NOT include any text outside the JSON object.
- All string values MUST be single-line.
- The sql field MUST be a single-line string or null.
- Do NOT include markdown, code fences, or explanations.

SQL rules (only if mode is sql):
- Generate a SELECT query only.
- Use the schema provided.
- Always filter by accountId = "{tenant_id}".

Return JSON in exactly this format:
{{
  "mode": "chat | clarification | sql",
  "response": "Natural language response",
  "sql": "SQL query if mode is sql, otherwise null"
}}

Database schema:
{schema_context}

User input:
{natural_language_query}

IMPORTANT:
Your response must start with '{{' and end with '}}'.
If you include any text outside the JSON object, the request will fail."""

_CONFIG_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = _CONFIG_DIR / "data" / "admin_config.json"

_lock = Lock()
_cached: Dict[str, Any] | None = None


def _default_config() -> Dict[str, Any]:
    return {
        "guardrails": {
            "allowed_tenant_ids": DEFAULT_ALLOWED_TENANT_IDS,
            "dangerous_keywords": DEFAULT_DANGEROUS_KEYWORDS,
            "sql_injection_patterns": DEFAULT_SQL_INJECTION_PATTERNS,
            "tenant_column": DEFAULT_TENANT_COLUMN,
        },
        "prompt_template": DEFAULT_PROMPT_TEMPLATE,
    }


def _load_from_file() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return _default_config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults so new keys get defaults
        default = _default_config()
        guardrails = {**default["guardrails"], **(data.get("guardrails") or {})}
        prompt = data.get("prompt_template") or default["prompt_template"]
        return {"guardrails": guardrails, "prompt_template": prompt}
    except Exception:
        return _default_config()


def _get_cached() -> Dict[str, Any]:
    global _cached
    with _lock:
        if _cached is None:
            _cached = _load_from_file()
        return _cached


def get_config() -> Dict[str, Any]:
    """Return current guardrails and prompt template (in-memory cache)."""
    return _get_cached()


def get_guardrails_config() -> Dict[str, Any]:
    """Return guardrails section only."""
    return _get_cached()["guardrails"].copy()


def get_prompt_template() -> str:
    """Return prompt template string."""
    return _get_cached()["prompt_template"]


def save_config(config: Dict[str, Any]) -> None:
    """
    Save guardrails and prompt template to file and refresh in-memory cache.
    Validates structure; on success, next get_config() returns the new values.
    """
    global _cached
    guardrails = config.get("guardrails")
    prompt_template = config.get("prompt_template")
    if not guardrails or not isinstance(guardrails, dict):
        raise ValueError("config.guardrails must be an object")
    if prompt_template is None or not isinstance(prompt_template, str):
        raise ValueError("config.prompt_template must be a string")
    if not prompt_template.strip():
        prompt_template = DEFAULT_PROMPT_TEMPLATE

    allowed = guardrails.get("allowed_tenant_ids")
    keywords = guardrails.get("dangerous_keywords")
    patterns = guardrails.get("sql_injection_patterns")
    column = guardrails.get("tenant_column")
    if not isinstance(allowed, list) or not all(isinstance(x, str) for x in allowed):
        raise ValueError("guardrails.allowed_tenant_ids must be a list of strings")
    if not isinstance(keywords, list) or not all(isinstance(x, str) for x in keywords):
        raise ValueError("guardrails.dangerous_keywords must be a list of strings")
    if not isinstance(patterns, list) or not all(isinstance(x, str) for x in patterns):
        raise ValueError("guardrails.sql_injection_patterns must be a list of strings")
    if not isinstance(column, str) or not column.strip():
        raise ValueError("guardrails.tenant_column must be a non-empty string")

    payload = {
        "guardrails": {
            "allowed_tenant_ids": allowed,
            "dangerous_keywords": keywords,
            "sql_injection_patterns": patterns,
            "tenant_column": column.strip(),
        },
        "prompt_template": prompt_template,
    }

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _cached = payload
