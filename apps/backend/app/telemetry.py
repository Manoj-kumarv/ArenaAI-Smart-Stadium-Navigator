"""
Telemetry simulator — background task that mutates zone density every 2-3s
and broadcasts updates over WebSocket to all connected clients.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from typing import Set

from fastapi import WebSocket

from app.models import Zone, ZoneDensityHistory, cap_density, density_to_color

logger = logging.getLogger(__name__)

# ─── Connected WebSocket clients ──────────────────────────────────────────────
_connections: Set[WebSocket] = set()


def register(ws: WebSocket) -> None:
    _connections.add(ws)


def unregister(ws: WebSocket) -> None:
    _connections.discard(ws)


async def _broadcast(payload: dict) -> None:
    dead = set()
    message = json.dumps(payload)
    for ws in list(_connections):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        unregister(ws)


# ─── Zone density simulation ──────────────────────────────────────────────────
# Each zone has a "base" density that drifts over time with Gaussian noise
_zone_bases: dict[str, float] = {}

# Zones that tend to get crowded (gates, concourses)
_HOT_ZONES = {"gate_a", "gate_b", "gate_c", "gate_d", "concourse_north", "concourse_south"}


def _init_bases(zones: list[Zone]) -> None:
    for z in zones:
        if z.id in _HOT_ZONES:
            _zone_bases[z.id] = random.uniform(0.55, 0.80)
        elif z.zone_type.value in ("medical", "volunteer_post"):
            _zone_bases[z.id] = random.uniform(0.05, 0.20)
        else:
            _zone_bases[z.id] = random.uniform(0.20, 0.60)


def _step_density(zone_id: str, current: float) -> float:
    """Random walk with mean-reversion toward the zone's base."""
    base = _zone_bases.get(zone_id, 0.4)
    # Mean-reversion + noise
    noise = random.gauss(0, 0.04)
    reversion = 0.05 * (base - current)
    new_val = current + noise + reversion
    return max(0.0, min(1.05, new_val))  # allow a tiny overshoot to test cap


# ─── Background simulator loop ────────────────────────────────────────────────

async def telemetry_loop(get_db_fn) -> None:
    """Runs forever as a FastAPI lifespan background task."""
    await asyncio.sleep(2)  # let app finish starting

    # Bootstrap zone bases
    db = next(get_db_fn())
    zones = db.query(Zone).all()
    _init_bases(zones)
    db.close()

    logger.info("Telemetry simulator started for %d zones", len(zones))

    while True:
        interval = random.uniform(2.0, 3.0)
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
                zone.updated_at = datetime.now(timezone.utc)

                # Record history (keep last ~200 rows per zone via periodic cleanup)
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
                    "ts": datetime.now(timezone.utc).isoformat(),
                })

            db.commit()

            # Broadcast to all WS clients
            await _broadcast({
                "type": "telemetry",
                "data": updates,
                "server_ts": datetime.now(timezone.utc).isoformat(),
            })

        except Exception as exc:
            logger.error("Telemetry loop error: %s", exc)
            db.rollback()
        finally:
            db.close()
