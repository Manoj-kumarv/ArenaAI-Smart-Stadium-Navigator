"""
Incidents router — CRUD, AI-powered resolution with transactional rollback,
audit logging, and paginated listing.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import (
    AuditAction, AuditLog, Incident, IncidentStatus, User, UserRole,
)
from app.schemas import (
    IncidentCreate, IncidentOut, IncidentPage, ResolveResponse,
)
from app.ai.orchestrator import orchestrate_incident

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=IncidentPage)
async def list_incidents(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
):
    q = db.query(Incident)
    if status_filter:
        q = q.filter(Incident.status == status_filter)
    total = q.count()
    items = (
        q.order_by(Incident.ai_severity_score.desc().nullslast(), Incident.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return IncidentPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.ops_staff))])
async def create_incident(
    payload: IncidentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
):
    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return incident


@router.post("/{incident_id}/resolve", response_model=ResolveResponse,
             dependencies=[Depends(require_role(UserRole.ops_staff))])
async def resolve_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
):
    """
    Transactional resolution workflow (Property 8 — rollback on failure):
    1. Fetch incident & validate state
    2. Write audit log (before action — append-only)
    3. Call AI agent
    4. Update incident status
    5. On any step failure → revert status to 'open', delete orphan audit row
    """
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    if incident.status == IncidentStatus.resolved:
        raise HTTPException(status_code=400, detail="Incident is already resolved.")

    original_status = incident.status
    audit_row: AuditLog | None = None

    try:
        # Step 1 — mark in_progress
        incident.status = IncidentStatus.in_progress
        db.flush()

        # Step 2 — write audit log BEFORE action
        audit_row = AuditLog(
            action=AuditAction.incident_resolve,
            user_id=current_user.id,
            incident_id=incident.id,
            zone_id=incident.zone_id,
            detail="Resolution initiated",
        )
        db.add(audit_row)
        db.flush()

        # Step 3 — call AI agent
        ai_result = await orchestrate_incident(
            incident.title,
            incident.description,
            incident.zone_id,
        )

        # Step 4 — update incident
        incident.status = IncidentStatus.resolved
        incident.ai_resolution = json.dumps(ai_result)
        incident.ai_severity_score = ai_result.get("confidence")
        incident.resolved_at = datetime.now(timezone.utc)

        # Update audit with result
        audit_row.detail = f"Resolved via AI. confidence={ai_result.get('confidence')}"
        db.commit()
        db.refresh(audit_row)

        return ResolveResponse(
            incident_id=incident.id,
            status=incident.status,
            ai_result=ai_result,
            audit_id=audit_row.id,
        )

    except Exception as exc:
        # Rollback — revert status, remove orphan audit row
        db.rollback()
        # Re-fetch and reset
        incident = db.get(Incident, incident_id)
        if incident:
            incident.status = original_status
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resolution failed and was rolled back: {str(exc)}",
        )


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(UserRole.ops_staff))])
async def delete_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    db.delete(incident)
    db.commit()
