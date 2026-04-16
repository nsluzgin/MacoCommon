"""Per-request trace_id context and logging integration."""

from __future__ import annotations

import logging
import re
import sys
from contextvars import ContextVar
from typing import TextIO
from uuid import UUID, uuid4

TraceId = UUID

_trace_id_var: ContextVar[TraceId | None] = ContextVar(
    "service_trace_id",
    default=None,
)

_configured: bool = False
_HEALTH_ACCESS_RE = re.compile(r"/health/(?:live|ready)")


def peek_trace_id() -> TraceId | None:
    """Return current trace_id without creating one."""
    return _trace_id_var.get()


def get_or_create_trace_id() -> TraceId:
    """Return the current trace_id, generating one when context is empty."""
    current = _trace_id_var.get()
    if current is not None:
        return current
    new_id = uuid4()
    _trace_id_var.set(new_id)
    return new_id


def get_trace_id() -> TraceId:
    """Backward-compatible alias for ``get_or_create_trace_id``."""
    return get_or_create_trace_id()


def get_trace_id_str() -> str:
    """Return trace_id as string, or empty string when context is missing."""
    trace_id = peek_trace_id()
    return str(trace_id) if trace_id is not None else ""


def set_trace_id(trace_id: TraceId) -> ContextVar.Token[TraceId | None]:
    """Set trace_id in the current context and return token for reset."""
    return _trace_id_var.set(trace_id)


def reset_trace_id(token: ContextVar.Token[TraceId | None]) -> None:
    """Reset trace_id context to previous value."""
    _trace_id_var.reset(token)


class TraceIdFilter(logging.Filter):
    """Inject optional trace attributes and suppress health endpoint access lines."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access" and _HEALTH_ACCESS_RE.search(record.getMessage()):
            return False

        trace_id = peek_trace_id()
        record.trace_fragment = f" [trace_id: {trace_id}]" if trace_id is not None else ""
        return True


def configure_logging(log_level: str, *, stream: TextIO | None = None) -> None:
    """Configure logging format with optional trace_id context.

    If ``stream`` is set, the default root ``StreamHandler`` uses it (e.g. ``sys.stderr``
    for CLI workers). Otherwise stdout is used.
    """
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
        out = stream if stream is not None else sys.stdout
        handler = logging.StreamHandler(out)
        root.addHandler(handler)

    formatter = logging.Formatter(
        fmt="[%(levelname)s][%(asctime)s]%(trace_fragment)s: %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
    )
    trace_filter = TraceIdFilter()

    # Apply to root handlers and common uvicorn loggers.
    for logger_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        for h in logger.handlers:
            h.setFormatter(formatter)
            h.addFilter(trace_filter)

    # Uvicorn attaches handlers to these; with propagate=True (default) each record is also
    # handled by ancestors (uvicorn → root), so access lines appear 3× and startup lines 2×.
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = False

    _configured = True
