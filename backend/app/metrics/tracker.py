"""
Metrics tracking for analytics dashboard.

Tracks:
- Total requests
- Errors by type
- SQL queries generated
- Chat/clarification responses
- Performance metrics (execution times)
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Any, Optional

# Thread-safe metrics storage
_metrics_lock = Lock()

# Counters
_total_requests = 0
_total_errors = 0
_total_sql_queries = 0
_total_chat_responses = 0
_total_clarification_responses = 0

# Error tracking by type
_error_counts: Dict[str, int] = defaultdict(int)

# Per-tenant counters (tenant_id -> counts)
_by_tenant: Dict[str, Dict[str, int]] = defaultdict(lambda: {
    "requests": 0,
    "errors": 0,
    "sql_queries": 0,
    "chat_responses": 0,
    "clarification_responses": 0,
})
_by_tenant_errors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

# Performance metrics
_query_execution_times: List[float] = []
_bedrock_call_times: List[float] = []

# Time-based tracking (last 24 hours)
_start_time = datetime.now()
_hourly_requests: Dict[str, int] = defaultdict(int)  # "YYYY-MM-DD HH" -> count
_hourly_errors: Dict[str, int] = defaultdict(int)    # "YYYY-MM-DD HH" -> count


def _get_current_hour_key() -> str:
    """Return a date-qualified hour key like '2026-03-26 14' to avoid midnight wrapping."""
    return datetime.now().strftime("%Y-%m-%d %H")


def _cleanup_old_data():
    """Remove data older than 24 hours."""
    global _query_execution_times, _bedrock_call_times, _hourly_requests, _hourly_errors
    cutoff = datetime.now() - timedelta(hours=24)

    # Prune hourly buckets older than 24 hours
    for key in list(_hourly_requests.keys()):
        try:
            if datetime.strptime(key, "%Y-%m-%d %H") < cutoff:
                del _hourly_requests[key]
        except ValueError:
            del _hourly_requests[key]
    for key in list(_hourly_errors.keys()):
        try:
            if datetime.strptime(key, "%Y-%m-%d %H") < cutoff:
                del _hourly_errors[key]
        except ValueError:
            del _hourly_errors[key]

    # Keep only recent performance data (last 1000 entries)
    if len(_query_execution_times) > 1000:
        _query_execution_times = _query_execution_times[-1000:]
    if len(_bedrock_call_times) > 1000:
        _bedrock_call_times = _bedrock_call_times[-1000:]


def increment_request_count(tenant_id: Optional[str] = None) -> None:
    """Increment total request counter and optionally per-tenant."""
    global _total_requests
    with _metrics_lock:
        _total_requests += 1
        _hourly_requests[_get_current_hour_key()] += 1
        if tenant_id:
            _by_tenant[tenant_id]["requests"] += 1


def increment_error_count(error_type: str = "unknown", tenant_id: Optional[str] = None) -> None:
    """Increment error counter and track error type; optionally per-tenant."""
    global _total_errors
    with _metrics_lock:
        _total_errors += 1
        _error_counts[error_type] += 1
        _hourly_errors[_get_current_hour_key()] += 1
        if tenant_id:
            _by_tenant[tenant_id]["errors"] += 1
            _by_tenant_errors[tenant_id][error_type] += 1


def increment_sql_query_count(tenant_id: Optional[str] = None) -> None:
    """Increment SQL query counter; optionally per-tenant."""
    global _total_sql_queries
    with _metrics_lock:
        _total_sql_queries += 1
        if tenant_id:
            _by_tenant[tenant_id]["sql_queries"] += 1


def increment_chat_count(tenant_id: Optional[str] = None) -> None:
    """Increment chat response counter; optionally per-tenant."""
    global _total_chat_responses
    with _metrics_lock:
        _total_chat_responses += 1
        if tenant_id:
            _by_tenant[tenant_id]["chat_responses"] += 1


def increment_clarification_count(tenant_id: Optional[str] = None) -> None:
    """Increment clarification response counter; optionally per-tenant."""
    global _total_clarification_responses
    with _metrics_lock:
        _total_clarification_responses += 1
        if tenant_id:
            _by_tenant[tenant_id]["clarification_responses"] += 1


def get_metrics_by_tenant(tenant_id: str) -> Dict[str, Any]:
    """Get metrics for a single tenant/account."""
    with _metrics_lock:
        t = _by_tenant.get(tenant_id, defaultdict(int))
        errors_by_type = dict(_by_tenant_errors.get(tenant_id, {}))
        requests = t.get("requests", 0)
        errors = t.get("errors", 0)
        return {
            "tenant_id": tenant_id,
            "requests": requests,
            "errors": errors,
            "sql_queries": t.get("sql_queries", 0),
            "chat_responses": t.get("chat_responses", 0),
            "clarification_responses": t.get("clarification_responses", 0),
            "success_rate": round(((requests - errors) / requests * 100), 2) if requests > 0 else 0,
            "errors_by_type": errors_by_type,
        }


def get_all_tenant_ids() -> List[str]:
    """Return list of tenant IDs that have at least one request."""
    with _metrics_lock:
        return list(_by_tenant.keys())


def record_query_execution_time(execution_time_ms: float) -> None:
    """Record SQL query execution time in milliseconds."""
    with _metrics_lock:
        _query_execution_times.append(execution_time_ms)
        _cleanup_old_data()


def record_bedrock_call_time(call_time_ms: float) -> None:
    """Record Bedrock API call time in milliseconds."""
    with _metrics_lock:
        _bedrock_call_times.append(call_time_ms)
        _cleanup_old_data()


def get_metrics() -> Dict[str, Any]:
    """
    Get current metrics snapshot.
    
    Returns:
        Dictionary with all metrics data
    """
    with _metrics_lock:
        _cleanup_old_data()
        
        # Calculate averages
        avg_query_time = (
            sum(_query_execution_times) / len(_query_execution_times)
            if _query_execution_times else 0
        )
        avg_bedrock_time = (
            sum(_bedrock_call_times) / len(_bedrock_call_times)
            if _bedrock_call_times else 0
        )
        
        # Calculate success rate
        success_rate = (
            ((_total_requests - _total_errors) / _total_requests * 100)
            if _total_requests > 0 else 0
        )
        
        # Get hourly data for last 24 hours (oldest → newest)
        now = datetime.now()
        hourly_data = []
        for i in range(23, -1, -1):
            slot = now - timedelta(hours=i)
            key = slot.strftime("%Y-%m-%d %H")
            hourly_data.append({
                "hour": slot.hour,
                "label": key,
                "requests": _hourly_requests.get(key, 0),
                "errors": _hourly_errors.get(key, 0),
            })
        
        uptime_seconds = (datetime.now() - _start_time).total_seconds()
        uptime_hours = uptime_seconds / 3600
        
        by_tenant_summary = {
            tid: {
                "requests": data["requests"],
                "errors": data["errors"],
                "sql_queries": data["sql_queries"],
                "chat_responses": data["chat_responses"],
                "clarification_responses": data["clarification_responses"],
                "success_rate": round(
                    ((data["requests"] - data["errors"]) / data["requests"] * 100), 2
                ) if data["requests"] > 0 else 0,
            }
            for tid, data in _by_tenant.items()
        }
        return {
            "summary": {
                "total_requests": _total_requests,
                "total_errors": _total_errors,
                "total_sql_queries": _total_sql_queries,
                "total_chat_responses": _total_chat_responses,
                "total_clarification_responses": _total_clarification_responses,
                "success_rate": round(success_rate, 2),
                "uptime_hours": round(uptime_hours, 2),
            },
            "errors": {
                "by_type": dict(_error_counts),
                "total": _total_errors,
            },
            "performance": {
                "avg_query_execution_time_ms": round(avg_query_time, 2),
                "avg_bedrock_call_time_ms": round(avg_bedrock_time, 2),
                "query_execution_samples": len(_query_execution_times),
                "bedrock_call_samples": len(_bedrock_call_times),
            },
            "hourly": hourly_data,
            "by_tenant": by_tenant_summary,
            "timestamp": datetime.now().isoformat(),
        }


