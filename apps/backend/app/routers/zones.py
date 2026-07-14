"""Zones router — digital twin state, AI analysis, zone actions."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import AuditAction, AuditLog, User, UserRole, Zone
from app.schemas import CrowdAnalysisResponse, ZoneActionRequest, ZoneOut
from app.ai.orchestrator import orchestrate_crowd

router = APIRouter(prefix="/api/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
async def list_zones(db: Annotated[Session, Depends(get_db)]):
    """Public endpoint — fan and ops_staff can read zone states."""
    return db.query(Zone).order_by(Zone.id).all()


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(zone_id: str, db: Annotated[Session, Depends(get_db)]):
    zone = db.get(Zone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    return zone


@router.post("/{zone_id}/analyse", response_model=CrowdAnalysisResponse)
async def analyse_zone(
    zone_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Any authenticated user can request crowd analysis."""
    zone = db.get(Zone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    result = await orchestrate_crowd(
        zone.id, zone.name, zone.density_pct, zone.capacity
    )
    return CrowdAnalysisResponse(**result)


@router.post("/action", dependencies=[Depends(require_role(UserRole.ops_staff))])
async def zone_action(
    payload: ZoneActionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
):
    """
    ops_staff only — broadcast, deploy_volunteers, update_signage.
    Writes audit log before executing action.
    """
    zone = db.get(Zone, payload.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")

    audit = AuditLog(
        action=AuditAction.zone_action,
        user_id=current_user.id,
        zone_id=payload.zone_id,
        detail=f"action={payload.action}; detail={payload.detail}",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "status": "ok",
        "action": payload.action,
        "zone_id": payload.zone_id,
        "audit_id": audit.id,
        "message": f"Action '{payload.action}' executed for zone '{zone.name}'.",
    }


@router.get("/kpi/summary")
async def kpi_summary(db: Annotated[Session, Depends(get_db)]):
    """KPI bar data — public read."""
    from app.models import Incident, IncidentStatus, ColorState
    zones = db.query(Zone).all()
    total_capacity = sum(z.capacity for z in zones)
    total_occupancy = sum(int(z.density_pct * z.capacity) for z in zones)
    active_incidents = db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.open, IncidentStatus.in_progress])
    ).count()
    critical_zones = sum(1 for z in zones if z.color_state == ColorState.critical)
    ai_actions = db.query(AuditLog).count()

    # Simulated wait time based on avg density
    avg_density = sum(z.density_pct for z in zones) / max(len(zones), 1)
    avg_wait = round(avg_density * 18, 1)  # 0-18 min scale

    return {
        "attendance": total_occupancy,
        "active_incidents": active_incidents,
        "avg_wait_minutes": avg_wait,
        "ai_actions_taken": ai_actions,
        "critical_zones": critical_zones,
    }
