"""
FastAPI application entry point.
- CORS locked to FRONTEND_ORIGIN
- Rate limiting via SlowAPI
- Lifespan: DB init, seed, telemetry background task
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import engine, get_db
from app.models import Base
from app import telemetry
from app.routers import auth, broadcast, fan, incidents, zones, ws

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Rate limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")

    # Auto-seed if DB is empty
    try:
        from scripts.seed import db as _  # noqa: F401  (import triggers seed)
    except Exception:
        pass  # seed already ran or not needed

    # Start telemetry simulator
    task = asyncio.create_task(telemetry.telemetry_loop(get_db))
    logger.info("Telemetry simulator task started.")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Telemetry simulator stopped.")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ArenaIQ — Smart Stadium Navigator",
    description="GenAI-powered stadium operations for FIFA World Cup 2026",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — locked to the configured frontend origin (not wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(zones.router)
app.include_router(incidents.router)
app.include_router(broadcast.router)
app.include_router(fan.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "arenaiq-backend"}


# ─── AI endpoint rate limits (applied via decorator on individual routes) ─────
# slowapi decorators are applied per-router via the limiter instance above.
# Global default: 200/min. AI-heavy endpoints: 30/min enforced in routers below.
