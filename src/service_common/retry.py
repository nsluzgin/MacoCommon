"""Configurable async retry for network calls with user-visible error codes."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import uuid4

from service_common.exceptions import UpstreamNetworkError

logger = logging.getLogger(__name__)

T = TypeVar("T")

_DEFAULT_TRANSIENT: tuple[type[BaseException], ...] = (
    OSError,
    ConnectionError,
    asyncio.TimeoutError,
    TimeoutError,
)


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    operation_name: str,
    attempts: int,
    interval_seconds: float,
    testing: bool,
    transient_exceptions: tuple[type[BaseException], ...] = _DEFAULT_TRANSIENT,
    on_retry: Callable[[], Awaitable[None]] | None = None,
    error_cls: type[UpstreamNetworkError] = UpstreamNetworkError,
) -> T:
    """
    Retry an async operation on transient exceptions.

    If all attempts fail, log and raise ``UpstreamNetworkError`` with a stable
    ``code`` (UUID hex) for correlation.
    """
    n = max(1, int(attempts))
    interval = float(interval_seconds)
    if testing:
        n = 1
        interval = 0.0

    code = uuid4().hex
    last_exc: BaseException | None = None

    for attempt in range(1, n + 1):
        try:
            return await operation()
        except transient_exceptions as exc:  # noqa: PERF203
            last_exc = exc
            if attempt >= n:
                logger.error(
                    "network_retry_exhausted code=%s operation=%s attempts=%s",
                    code,
                    operation_name,
                    n,
                    exc_info=True,
                )
                raise error_cls(
                    code=code,
                    message="Network error while contacting an upstream service.",
                ) from exc

            logger.warning(
                "network_retry code=%s operation=%s attempt=%s/%s",
                code,
                operation_name,
                attempt,
                n,
            )
            if on_retry is not None:
                await on_retry()
            if interval > 0:
                await asyncio.sleep(interval)

    raise error_cls(
        code=code,
        message="Network error while contacting an upstream service.",
    ) from last_exc
