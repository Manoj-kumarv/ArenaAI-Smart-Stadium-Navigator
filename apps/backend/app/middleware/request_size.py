"""
Request size limiter middleware.

Protects the application against Denial of Service (DoS) attacks
by rejecting request bodies larger than a configured limit.
"""
from __future__ import annotations

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing a limit on request body size."""

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        """Intercept the request and check the Content-Length header.

        Args:
            request: The incoming request.
            call_next: Next handler in chain.

        Returns:
            An HTTP 413 response if size limit exceeded, otherwise delegates.
        """
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > settings.MAX_CONTENT_LENGTH:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": (
                                f"Request entity too large. "
                                f"Max allowed: {settings.MAX_CONTENT_LENGTH} bytes."
                            )
                        },
                    )
            except ValueError:
                # Malformed header, let downstream handle or reject
                pass

        return await call_next(request)
