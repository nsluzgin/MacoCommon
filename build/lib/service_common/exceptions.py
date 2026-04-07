"""Exceptions shared across HTTP services."""


class UpstreamNetworkError(Exception):
    """Transient upstream connectivity failure after retries (HTTP 500)."""

    def __init__(
        self,
        *,
        code: str,
        message: str = "Network error while contacting an upstream service.",
        status_code: int = 500,
    ) -> None:
        """Store opaque error code and response fields."""
        self.code = code
        self.status_code = status_code
        self.message = message
        super().__init__(message)
