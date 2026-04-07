"""Build consistent HTTP 500 responses for unexpected failures.

For risky operations: catch exceptions, log an `error code` with stack trace,
and return the same code to the user.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _extract_error_code(exc: BaseException) -> str:
    """
    Return a unique random identifier to expose to the client.

    The returned code must be a UUID (or UUID-like hex string).
    Some upstream libraries expose a non-unique error "code" (e.g. MinIO
    ``InvalidBucketName``), so we must not forward that to the client.
    """
    code = getattr(exc, "code", None)
    if isinstance(code, str) and len(code) == 32:
        # uuid4().hex is a 32-char lowercase hex string.
        lowered = code.lower()
        if all(ch in "0123456789abcdef" for ch in lowered):
            return lowered
    return uuid4().hex


def log_error_code_with_stack(exc: BaseException) -> str:
    """Log ``error code=...`` and include full stack trace."""
    code = _extract_error_code(exc)
    # logger.exception() appends the current stack trace to the log message.
    logger.exception("error code=%s", code)
    return code


def internal_server_error_response(*, code: str, message: str | None = None) -> Any:
    """Return JSON error envelope including the same ``code``."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "Message": message or "Internal server error",
            "code": code,
        },
    )
