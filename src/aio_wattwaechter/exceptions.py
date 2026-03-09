"""Exceptions for the aio-wattwaechter library."""

from __future__ import annotations


class WattwaechterError(Exception):
    """Base exception for WattWächter API errors."""


class WattwaechterConnectionError(WattwaechterError):
    """Error when the device is unreachable or returns unexpected responses."""


class WattwaechterAuthenticationError(WattwaechterError):
    """Error when authentication fails (invalid or missing token)."""


class WattwaechterRateLimitError(WattwaechterError):
    """Error when the device rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Initialize with optional retry-after hint."""
        super().__init__(message)
        self.retry_after = retry_after


class WattwaechterNoDataError(WattwaechterError):
    """Error when no data is available (HTTP 204)."""
