"""Correlation ID middleware for request tracing.

Generates or propagates a unique X-Correlation-ID header for each request,
enabling end-to-end request tracking across logs, AI agent calls,
and downstream services.

Usage:
    The correlation ID is automatically attached to:
    - All log entries via the structured logging configuration
    - Response headers for client-side correlation
    - AI agent calls for tracing GenAI request flows
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variable storing the current request's correlation ID.
# Accessible from any async code within the same request context.
correlation_id_var: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)

CORRELATION_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str | None:
    """Retrieve the current request's correlation ID from context.

    Returns:
        The correlation ID string, or None if called outside a request context.

    """
    return correlation_id_var.get()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique correlation ID to each request.

    If the incoming request includes an ``X-Correlation-ID`` header,
    that value is reused (supporting distributed tracing). Otherwise,
    a new UUID4 is generated.

    The correlation ID is stored in a ``ContextVar`` so it can be accessed
    from any part of the application during request processing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Extract or generate a correlation ID and propagate it.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response with the X-Correlation-ID header attached.

        """
        # Reuse client-provided correlation ID or generate a new one
        cid = request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))
        correlation_id_var.set(cid)

        response: Response = await call_next(request)
        response.headers[CORRELATION_HEADER] = cid

        return response
