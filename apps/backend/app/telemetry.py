"""Telemetry simulator and WebSocket broadcast engine.

Simulates drift in zone density over time and pushes telemetry updates
via active WebSocket connections.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.constants import (
    SIMULATION_DENSITY_MAX_OVERSHOOT,
    SIMULATION_MEAN_REVERSION_RATE,
    SIMULATION_NOISE_STD_DEV,
    TELEMETRY_CLEANUP_INTERVAL_SECONDS,
    TELEMETRY_HISTORY_RETENTION_SECONDS,
    TELEMETRY_INTERVAL_MAX_SECONDS,
    TELEMETRY_INTERVAL_MIN_SECONDS,
    TELEMETRY_STARTUP_DELAY_SECONDS,
)
from app.models import Zone, ZoneDensityHistory, cap_density, density_to_color

logger = logging.getLogger(__name__)

# List of currently connected WebSocket clients
_connections: set[WebSocket] = set()

# Drift baseline density values per zone
_zone_bases: dict[str, float] = {}

# Zones targeting higher baseline crowd levels (e.g. key exit/entry areas)
_HOT_ZONES = {"gate_a", "gate_b", "gate_c", "gate_d", "concourse_north", "concourse_south"}


def register(ws: WebSocket) -> None:
    """Register a new active WebSocket client connection.

    Args:
        ws: The new WebSocket connection.

    """
    _connections.add(ws)
    logger.debug("Registered new WebSocket connection. Active count: %d", len(_connections))


def unregister(ws: WebSocket) -> None:
    """Remove a disconnected WebSocket client from the register.

    Args:
        ws: The WebSocket connection to remove.

    """
    _connections.discard(ws)
    logger.debug("Unregistered WebSocket connection. Active count: %d", len(_connections))


async def _broadcast(payload: dict[str, Any]) -> None:
    """Broadcast JSON payload to all active connections.

    Args:
        payload: Data dictionary to broadcast.

    """
    dead: set[WebSocket] = set()
    message = json.dumps(payload)
    for ws in list(_connections):
        try:
            await ws.send_text(message)
        except Exception as exc:
            logger.debug("Failed to send message over WS: %s", exc)
            dead.add(ws)
    for ws in dead:
        unregister(ws)


def _init_bases(zones: list[Zone]) -> None:
    """Initialize random walk baselines for each zone type.

    Args:
        zones: The database zones list.

    """
    for z in zones:
        if z.id in _HOT_ZONES:
            _zone_bases[z.id] = random.uniform(0.55, 0.80)
        elif z.zone_type.value in ("medical", "volunteer_post"):
            _zone_bases[z.id] = random.uniform(0.05, 0.20)
        else:
            _zone_bases[z.id] = random.uniform(0.20, 0.60)


def _step_density(zone_id: str, current: float) -> float:
    """Perform Gaussian random walk drift with mean reversion toward baseline.

    Args:
        zone_id: Target zone ID.
        current: Current density fraction.

    Returns:
        The new calculated density fraction.

    """
    base = _zone_bases.get(zone_id, 0.4)
    noise = random.gauss(0, SIMULATION_NOISE_STD_DEV)
    reversion = SIMULATION_MEAN_REVERSION_RATE * (base - current)
    new_val = current + noise + reversion
    return max(0.0, min(SIMULATION_DENSITY_MAX_OVERSHOOT, new_val))


async def telemetry_loop(
    get_db_fn: Callable[[], Generator[Session, None, None]],
) -> None:
    """Execute the background telemetry simulation loop.

    Runs indefinitely. Generates and commits updates, deletes older history
    rows, and broadcasts updates over WebSockets.

    Args:
        get_db_fn: Function returning a database session generator.

    """
    await asyncio.sleep(TELEMETRY_STARTUP_DELAY_SECONDS)

    # Bootstrap zone bases
    db = next(get_db_fn())
    zones = db.query(Zone).all()
    _init_bases(zones)
    db.close()

    logger.info("Telemetry simulator started for %d zones", len(zones))
    last_cleanup = datetime.utcnow()

    while True:
        interval = random.uniform(TELEMETRY_INTERVAL_MIN_SECONDS, TELEMETRY_INTERVAL_MAX_SECONDS)
        await asyncio.sleep(interval)

        db = next(get_db_fn())
        try:
            zones = db.query(Zone).all()
            updates = []

            for zone in zones:
                raw = _step_density(zone.id, zone.density_pct)
                capped, was_capped = cap_density(raw)
                color = density_to_color(capped)

                zone.density_pct = capped
                zone.color_state = color
                zone.updated_at = datetime.now(UTC)

                # Record history
                db.add(ZoneDensityHistory(
                    zone_id=zone.id,
                    density_pct=capped,
                    color_state=color,
                ))

                updates.append({
                    "zone_id": zone.id,
                    "density_pct": round(capped, 4),
                    "color_state": color.value,
                    "was_capped": was_capped,
                    "ts": datetime.now(UTC).isoformat(),
                })

            # Periodic cleanup of old history rows
            now = datetime.utcnow()
            if (now - last_cleanup).total_seconds() > TELEMETRY_CLEANUP_INTERVAL_SECONDS:
                cutoff = now - timedelta(seconds=TELEMETRY_HISTORY_RETENTION_SECONDS)
                db.query(ZoneDensityHistory).filter(ZoneDensityHistory.recorded_at < cutoff).delete()
                last_cleanup = now

            db.commit()

            # Broadcast to all WS clients
            await _broadcast({
                "type": "telemetry",
                "data": updates,
                "server_ts": datetime.now(UTC).isoformat(),
            })

        except Exception as exc:
            logger.error("Telemetry loop error: %s", exc)
            db.rollback()
        finally:
            db.close()
