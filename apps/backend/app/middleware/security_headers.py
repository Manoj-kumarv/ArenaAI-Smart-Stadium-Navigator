"""
Security headers middleware for the ArenaIQ backend.

Adds defense-in-depth HTTP security headers to all responses,
mitigating XSS, clickjacking, MIME sniffing, and other common
web application vulnerabilities.

Headers applied:
    - Content-Security-Policy: Restricts resource loading origins
    - Strict-Transport-Security: Enforces HTTPS connections
    - X-Content-Type-Options: Prevents MIME-type sniffing
    - X-Frame-Options: Prevents clickjacking via iframes
    - X-XSS-Protection: Legacy XSS filter (defense-in-depth)
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Disables unnecessary browser features
    - Cache-Control: Prevents caching of API responses with sensitive data

References:
    - OWASP Secure Headers: https://owasp.org/www-project-secure-headers/
    - MDN Security Headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
"""
from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that injects security headers into every HTTP response.

    This middleware implements defense-in-depth security by adding
    multiple protective headers that browsers use to restrict
    potentially dangerous behaviors.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        """Process the request and add security headers to the response.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            The HTTP response with security headers applied.
        """
        response: Response = await call_next(request)

        # Prevent MIME-type sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking via iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS filter (defense-in-depth for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS for 1 year including subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Content Security Policy — restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )

        # Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=()"
        )

        # Prevent caching of API responses (sensitive data protection)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )

        return response
