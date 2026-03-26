"""Metrics tracking module for analytics dashboard."""

from app.metrics.tracker import (
    get_metrics,
    get_metrics_by_tenant,
    get_all_tenant_ids,
    increment_request_count,
    increment_error_count,
    increment_sql_query_count,
    increment_chat_count,
    increment_clarification_count,
    record_query_execution_time,
    record_bedrock_call_time,
    record_token_usage,
)

__all__ = [
    "get_metrics",
    "get_metrics_by_tenant",
    "get_all_tenant_ids",
    "increment_request_count",
    "increment_error_count",
    "increment_sql_query_count",
    "increment_chat_count",
    "increment_clarification_count",
    "record_query_execution_time",
    "record_bedrock_call_time",
    "record_token_usage",
]


