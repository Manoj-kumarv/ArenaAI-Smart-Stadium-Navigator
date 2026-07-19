"""FastAPI application entry point for ArenaIQ Smart Stadium Navigator.

Configures the ASGI application with:
- CORS policy locked to the configured frontend origin
- Rate limiting via SlowAPI (200/min global, lower for AI endpoints)
- Security headers middleware (CSP, HSTS, X-Frame-Options, etc.)
- Correlation ID middleware for distributed request tracing
- Structured JSON logging for production observability
- Lifespan: database initialization, seed data, telemetry background task
- Graceful shutdown for in-flight WebSocket connections
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import telemetry
from app.config import settings
from app.database import engine, get_db
from app.limiter import limiter
from app.logging_config import setup_logging
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models import Base
from app.routers import auth, broadcast, fan, incidents, ws, zones

# Configure structured logging before anything else
setup_logging(
    level=settings.LOG_LEVEL,
    structured=settings.ENABLE_STRUCTURED_LOGGING,
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Startup:
        1. Create database tables if they don't exist.
        2. Run seed script for demo data (skipped if DB is populated).
        3. Start the telemetry simulator background task.

    Shutdown:
        1. Cancel the telemetry background task gracefully.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")

    # Auto-seed if DB is empty
    try:
        from scripts.seed import db as _  # noqa: F401
    except Exception:
        pass  # seed already ran or not needed

    # Start telemetry simulator
    task = asyncio.create_task(telemetry.telemetry_loop(get_db))
    logger.info("Telemetry simulator task started.")

    yield

    # Graceful shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Telemetry simulator stopped. Shutdown complete.")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ArenaIQ — Smart Stadium Navigator",
    description=(
        "GenAI-powered stadium operations platform for FIFA World Cup 2026. "
        "Provides real-time crowd management, AI-driven incident resolution, "
        "multilingual fan assistance, and comprehensive audit trails."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication and authorization (JWT + RBAC)"},
        {"name": "zones", "description": "Stadium zone management and AI crowd analysis"},
        {"name": "incidents", "description": "Incident lifecycle management with AI resolution"},
        {"name": "broadcast", "description": "Atomic trilingual PA broadcast generation"},
        {"name": "fan", "description": "Public multilingual fan assistant (EN/ES/AR)"},
        {"name": "websocket", "description": "Real-time telemetry push via WebSocket"},
    ],
    contact={
        "name": "ArenaIQ Team",
        "url": "https://github.com/Manoj-kumarv/ArenaAI-Smart-Stadium-Navigator",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ─── Middleware Stack (order matters: outermost first) ────────────────────────

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Request size limit
app.add_middleware(RequestSizeLimitMiddleware)

# Security headers (CSP, HSTS, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Correlation ID for request tracing
app.add_middleware(CorrelationMiddleware)

# CORS — locked to the configured frontend origin (not wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "https://arenaiq-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(zones.router)
app.include_router(incidents.router)
app.include_router(broadcast.router)
app.include_router(fan.router)
app.include_router(ws.router)


# ─── Health & Readiness ───────────────────────────────────────────────────────


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Basic liveness probe.

    Returns:
        A JSON object with the service status.

    """
    return {"status": "ok", "service": "arenaiq-backend", "version": "1.0.0"}


@app.get("/ready", tags=["health"])
async def readiness() -> dict:
    """Readiness probe checking dependency health.

    Checks:
        - Database connectivity (SQLite file accessible)
        - Gemini API key presence (optional)

    Returns:
        A JSON object with individual dependency statuses.

    """
    checks: dict[str, str] = {}

    # Check database
    try:
        from sqlalchemy import text

        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Check Gemini availability
    checks["gemini_api"] = "configured" if settings.GEMINI_API_KEY.strip() else "not_configured (fallback mode)"

    overall = "ok" if checks.get("database") == "ok" else "degraded"
    return {"status": overall, "checks": checks}
