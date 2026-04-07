"""FastAPI middleware: propagate ``X-Trace-Id`` and bind trace context."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from service_common.tracing import get_trace_id, reset_trace_id, set_trace_id


def register_trace_id_middleware(app: FastAPI) -> None:
    """Attach middleware that reads or generates ``X-Trace-Id`` per request."""

    @app.middleware("http")
    async def _trace_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        header_value = request.headers.get("X-Trace-Id")
        if header_value:
            try:
                trace_id = UUID(header_value)
            except Exception:
                trace_id = get_trace_id()
        else:
            trace_id = get_trace_id()

        token = set_trace_id(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-Id"] = str(trace_id)
            return response
        finally:
            reset_trace_id(token)
