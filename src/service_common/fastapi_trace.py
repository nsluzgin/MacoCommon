"""FastAPI middleware: propagate ``X-Trace-Id`` and bind trace context."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from service_common.tracing import get_or_create_trace_id, reset_trace_id, set_trace_id

_TRACE_ID_MAX_LEN = 64


def _parse_trace_id_header(raw_value: str | None) -> UUID | None:
    """Return parsed UUID for trusted header values."""
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value or len(value) > _TRACE_ID_MAX_LEN:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def register_trace_id_middleware(app: FastAPI) -> None:
    """Attach middleware that reads or generates ``X-Trace-Id`` per request."""

    @app.middleware("http")
    async def _trace_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        trace_id = _parse_trace_id_header(request.headers.get("X-Trace-Id"))
        if trace_id is None:
            trace_id = get_or_create_trace_id()

        token = set_trace_id(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-Id"] = str(trace_id)
            return response
        finally:
            reset_trace_id(token)
