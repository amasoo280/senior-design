"""
Redact SQL and internal identifiers from text exposed to end users
(thinking stream, validation reasoning).

The model may echo SQL, tenant IDs, UUIDs, or other identifiers in its
reasoning; this layer strips or replaces those before SSE payloads leave
the server.
"""

from __future__ import annotations

import re
from typing import Optional

_UUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_HEX24 = re.compile(r"\b[0-9a-fA-F]{24}\b")

_FENCED = re.compile(r"```[\s\S]*?```")
# Unclosed ``` fence (model often omits closing backticks) — drop remainder as code/SQL.
_UNCLOSED_FENCE = re.compile(r"```[\s\S]*$")
_INLINE_LONG = re.compile(r"`[^`\n]{12,}`")

# Semicolon-terminated SQL statements (common in model output)
_SQL_PATTERNS = [
    re.compile(r"(?is)\bselect\b[\s\S]*?\bfrom\b[\s\S]*?;"),
    re.compile(r"(?is)\binsert\s+into\b[\s\S]*?;"),
    re.compile(r"(?is)\bupdate\b[\s\S]*?\bset\b[\s\S]*?;"),
    re.compile(r"(?is)\bdelete\s+from\b[\s\S]*?;"),
    re.compile(
        r"(?is)\bwith\s+[a-zA-Z_][\w]*\s+as\s*\([\s\S]*?\)\s*\bselect\b[\s\S]*?;"
    ),
]

# SQL-like runs without a trailing semicolon (bounded to limit collateral damage)
_SQL_UNTERMINATED = [
    re.compile(
        r"(?is)(?:^|[\n])(\s{0,8}select\s+[\s\S]{1,12000}?\s+from\s+[\s\S]{1,12000}?)(?=\n\n|\Z)"
    ),
    # Same line as other text: table-like token after FROM (skip common English "from the …")
    re.compile(
        r"(?is)\bselect\b[\s\S]{1,35000}?\bfrom\b\s+(?!the\b)(?:[`\"\[\]]?"
        r"[A-Za-z_][\w`\"\[\]]*[`\"\]]?)[\s\S]{0,35000}?(?=;|\Z|\n\n)"
    ),
]

_TENANT_EQ = re.compile(
    r"(?i)\btenant_id\b\s*=\s*['\"][^'\"]{0,400}['\"]"
)

# id / uuid style equality with quoted or bare opaque values
_OPAQUE_ID_EQ = re.compile(
    r"(?i)\b(?:uuid|account_?id|resource_?id|user_?id|clouduuid|anyuuid)\b\s*=\s*['\"]?[0-9a-fA-F\-]{8,}['\"]?"
)


def sanitize_thinking_text(text: str, tenant_id: Optional[str] = None) -> str:
    """
    Return a copy of ``text`` safe to show in the UI thinking panel.

    Redacts fenced code, SQL-shaped fragments, UUIDs / 24-char hex ids,
    tenant id literals, and common ``column = '<opaque id>'`` patterns.
    """
    if not text:
        return text

    t = text

    t = _FENCED.sub(" ", t)
    t = _UNCLOSED_FENCE.sub(" ", t)
    t = _INLINE_LONG.sub(" ", t)

    if tenant_id:
        t = t.replace(tenant_id, "[tenant]")

    for _ in range(24):
        orig = t
        for pat in _SQL_PATTERNS:
            t = pat.sub(" [query omitted] ", t)
        if t == orig:
            break

    for pat in _SQL_UNTERMINATED:
        t = pat.sub(" [query omitted] ", t)

    t = _TENANT_EQ.sub("tenant_id = [omitted]", t)
    t = _OPAQUE_ID_EQ.sub("[id] = [omitted]", t)
    t = _UUID.sub("[id]", t)
    t = _HEX24.sub("[id]", t)

    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
