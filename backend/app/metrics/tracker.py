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
from typing import Dict, List, Any

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

# Performance metrics
_query_execution_times: List[float] = []
_bedrock_call_times: List[float] = []

# Time-based tracking (last 24 hours)
_start_time = datetime.now()
_hourly_requests: Dict[int, int] = defaultdict(int)  # hour -> count
_hourly_errors: Dict[int, int] = defaultdict(int)  # hour -> count


def _get_current_hour() -> int:
    """Get current hour as integer (0-23)."""
    return datetime.now().hour


def _cleanup_old_data():
    """Remove data older than 24 hours."""
    global _query_execution_times, _bedrock_call_times
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    # Keep only recent performance data (last 1000 entries)
    if len(_query_execution_times) > 1000:
        _query_execution_times = _query_execution_times[-1000:]
    if len(_bedrock_call_times) > 1000:
        _bedrock_call_times = _bedrock_call_times[-1000:]


def increment_request_count() -> None:
    """Increment total request counter."""
    global _total_requests
    with _metrics_lock:
        _total_requests += 1
        hour = _get_current_hour()
        _hourly_requests[hour] += 1


def increment_error_count(error_type: str = "unknown") -> None:
    """Increment error counter and track error type."""
    global _total_errors
    with _metrics_lock:
        _total_errors += 1
        _error_counts[error_type] += 1
        hour = _get_current_hour()
        _hourly_errors[hour] += 1


def increment_sql_query_count() -> None:
    """Increment SQL query counter."""
    global _total_sql_queries
    with _metrics_lock:
        _total_sql_queries += 1


def increment_chat_count() -> None:
    """Increment chat response counter."""
    global _total_chat_responses
    with _metrics_lock:
        _total_chat_responses += 1


def increment_clarification_count() -> None:
    """Increment clarification response counter."""
    global _total_clarification_responses
    with _metrics_lock:
        _total_clarification_responses += 1


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
        
        # Get hourly data for last 24 hours
        hourly_data = []
        current_hour = _get_current_hour()
        for i in range(24):
            hour = (current_hour - i) % 24
            hourly_data.append({
                "hour": hour,
                "requests": _hourly_requests.get(hour, 0),
                "errors": _hourly_errors.get(hour, 0),
            })
        hourly_data.reverse()  # Oldest to newest
        
        uptime_seconds = (datetime.now() - _start_time).total_seconds()
        uptime_hours = uptime_seconds / 3600
        
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
            "timestamp": datetime.now().isoformat(),
        }


