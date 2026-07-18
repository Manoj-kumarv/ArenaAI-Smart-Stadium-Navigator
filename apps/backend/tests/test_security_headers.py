from __future__ import annotations


def test_security_headers_present(client):
    """Assert that secure headers are injected into every response by the middleware."""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "max-age=31536000" in response.headers.get("Strict-Transport-Security", "")
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers.get("Permissions-Policy", "")


def test_sensitive_headers_not_cached(client):
    """Assert that API endpoints disallow client caching of potentially sensitive info."""
    response = client.get("/api/zones")
    assert "no-store" in response.headers.get("Cache-Control", "")
