"""Per-request trace_id context and logging integration."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Final
from uuid import UUID, uuid4

TraceId = UUID

_trace_id_var: ContextVar[TraceId | None] = ContextVar(
    "service_trace_id",
    default=None,
)

_configured: bool = False

_DEFAULT_TRACE_ID_FALLBACK: Final[str] = "00000000-0000-0000-0000-000000000000"


def get_trace_id() -> TraceId:
    """Return the current request trace_id, generating it if missing."""
    current = _trace_id_var.get()
    if current is not None:
        return current
    new_id = uuid4()
    _trace_id_var.set(new_id)
    return new_id


def set_trace_id(trace_id: TraceId) -> ContextVar.Token[TraceId | None]:
    """Set trace_id in the current context and return token for reset."""
    return _trace_id_var.set(trace_id)


def reset_trace_id(token: ContextVar.Token[TraceId | None]) -> None:
    """Reset trace_id context to previous value."""
    _trace_id_var.reset(token)


def get_trace_id_str() -> str:
    """Return trace_id formatted for logs."""
    trace_id = _trace_id_var.get()
    if trace_id is None:
        return _DEFAULT_TRACE_ID_FALLBACK
    return str(trace_id)


class TraceIdFilter(logging.Filter):
    """Inject trace_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id_str()
        return True


def configure_logging(log_level: str) -> None:
    """Configure logging format so every log message contains trace_id."""
    global _configured
    if _configured:
        return

    level = logging.getLevelName(log_level.upper())
    # If parsing fails, keep INFO default.
    if isinstance(level, str):
        level = logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    # Ensure there's at least one handler.
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        root.addHandler(handler)

    formatter = logging.Formatter(
        fmt="[%(levelname)s][%(asctime)s] [trace_id: %(trace_id)s]: %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
    )
    trace_filter = TraceIdFilter()

    # Apply to root handlers and common uvicorn loggers.
    for logger_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        for h in logger.handlers:
            h.setFormatter(formatter)
            h.addFilter(trace_filter)
        # Keep propagation so filters/handlers on root apply consistently.
        logger.propagate = True

    _configured = True
