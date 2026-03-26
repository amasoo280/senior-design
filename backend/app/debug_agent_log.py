"""NDJSON debug log for Cursor debug mode (no secrets/PII)."""
import json
import time
from pathlib import Path

_LOG = Path(__file__).resolve().parent.parent.parent / ".cursor" / "debug.log"


def agent_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    try:
        payload = {
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
