"""Zones router.

Manages Digital Twin states, AI crowd analysis, and stadium zone actions.
"""
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.orchestrator import orchestrate_crowd
from app.auth import get_current_user, require_role
from app.constants import KPI_WAIT_TIME_SCALE_FACTOR
from app.database import get_db
from app.exceptions import NotFoundError
from app.limiter import limiter
from app.models import AuditAction, AuditLog, ColorState, Incident, IncidentStatus, User, UserRole, Zone
from app.schemas import (
    CrowdAnalysisResponse,
    KPIResponse,
    ZoneActionRequest,
    ZoneActionResponse,
    ZoneOut,
)

router = APIRouter(prefix="/api/zones", tags=["zones"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ZoneOut])
async def list_zones(db: Annotated[Session, Depends(get_db)]) -> list[Zone]:
    """Retrieve the current status of all stadium zones.

    Accessible to both fans and staff.

    Args:
        db: Database session.

    Returns:
        A list of Zone entities representing the current stadium state.

    """
    return db.query(Zone).order_by(Zone.id).all()


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(
    zone_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Zone:
    """Retrieve status details for a specific stadium zone by ID.

    Args:
        zone_id: The unique string identifier of the zone.
        db: Database session.

    Returns:
        The Zone entity.

    Raises:
        NotFoundError: If the zone does not exist.

    """
    zone = db.get(Zone, zone_id)
    if not zone:
        raise NotFoundError("Zone", zone_id).to_http_exception()
    return zone


@router.post("/{zone_id}/analyse", response_model=CrowdAnalysisResponse)
@limiter.limit("30/minute")
async def analyse_zone(
    request: Request,
    zone_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Triggers an AI-driven crowd density analysis for the specified zone.

    Enforces rate limits.

    Args:
        request: The incoming request (for rate limiting).
        zone_id: ID of the zone to analyze.
        db: Database session.
        current_user: Authenticated user (fan or ops staff).

    Returns:
        Crowd analysis containing cause, recommendation, confidence, and used_ai.

    Raises:
        NotFoundError: If the zone does not exist.

    """
    zone = db.get(Zone, zone_id)
    if not zone:
        raise NotFoundError("Zone", zone_id).to_http_exception()
    result = await orchestrate_crowd(
        zone.id, zone.name, zone.density_pct, zone.capacity
    )
    return result


@router.post(
    "/action",
    response_model=ZoneActionResponse,
    dependencies=[Depends(require_role(UserRole.ops_staff))],
)
async def zone_action(
    payload: ZoneActionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
) -> dict[str, Any]:
    """Execute a stadium operational action (e.g. PA broadcast, volunteers).

    Only permitted for ops_staff. Logs action to the audit log.

    Args:
        payload: Details of the action to take.
        db: Database session.
        current_user: Authenticated staff member.

    Returns:
        A dictionary containing action outcome details.

    Raises:
        NotFoundError: If the target zone does not exist.

    """
    zone = db.get(Zone, payload.zone_id)
    if not zone:
        raise NotFoundError("Zone", payload.zone_id).to_http_exception()

    audit = AuditLog(
        action=AuditAction.zone_action,
        user_id=current_user.id,
        zone_id=payload.zone_id,
        detail=f"action={payload.action}; detail={payload.detail}",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    logger.info(
        "Zone action '%s' executed for zone '%s' by user '%s'",
        payload.action,
        zone.name,
        current_user.username,
    )
    return {
        "status": "ok",
        "action": payload.action,
        "zone_id": payload.zone_id,
        "audit_id": audit.id,
        "message": f"Action '{payload.action}' executed for zone '{zone.name}'.",
    }


@router.get("/kpi/summary", response_model=KPIResponse)
async def kpi_summary(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Retrieve real-time stadium operations KPI summaries.

    Calculates attendance, active incidents, wait times, etc.
    Accessible to all users.

    Args:
        db: Database session.

    Returns:
        KPI metrics for the dashboard.

    """
    zones = db.query(Zone).all()
    total_occupancy = sum(int(z.density_pct * z.capacity) for z in zones)
    active_incidents = db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.open, IncidentStatus.in_progress])
    ).count()
    critical_zones = sum(1 for z in zones if z.color_state == ColorState.critical)
    ai_actions = db.query(AuditLog).count()

    # Simulated wait time based on avg density
    avg_density = sum(z.density_pct for z in zones) / max(len(zones), 1)
    avg_wait = round(avg_density * KPI_WAIT_TIME_SCALE_FACTOR, 1)

    return {
        "attendance": total_occupancy,
        "active_incidents": active_incidents,
        "avg_wait_minutes": avg_wait,
        "ai_actions_taken": ai_actions,
        "critical_zones": critical_zones,
    }
