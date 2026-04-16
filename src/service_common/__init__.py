"""Reusable building blocks for FastAPI-style microservices."""

from service_common.exceptions import UpstreamNetworkError
from service_common.fastapi_trace import register_trace_id_middleware
from service_common.internal_error import (
    internal_server_error_response,
    log_error_code_with_stack,
)
from service_common.retry import retry_async, retry_sync
from service_common.tracing import (
    TraceIdFilter,
    configure_logging,
    get_trace_id,
    get_trace_id_str,
    peek_trace_id,
    reset_trace_id,
    set_trace_id,
)

__all__ = [
    "TraceIdFilter",
    "UpstreamNetworkError",
    "configure_logging",
    "get_trace_id",
    "get_trace_id_str",
    "peek_trace_id",
    "internal_server_error_response",
    "log_error_code_with_stack",
    "register_trace_id_middleware",
    "reset_trace_id",
    "retry_async",
    "retry_sync",
    "set_trace_id",
]
