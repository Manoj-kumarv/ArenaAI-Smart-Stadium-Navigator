"""Incidents router.

Handles incident creation, retrieval, deletion, and AI-powered resolution.
Ensures transaction safety and immutable audit logging.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.ai.filters import check_pii_in_input, check_prompt_injection
from app.ai.orchestrator import orchestrate_incident
from app.auth import get_current_user, require_role
from app.database import get_db
from app.exceptions import AlreadyResolvedError, NotFoundError, ResolutionRollbackError
from app.limiter import limiter
from app.models import (
    AuditAction,
    AuditLog,
    Incident,
    IncidentStatus,
    User,
    UserRole,
)
from app.schemas import (
    IncidentCreate,
    IncidentOut,
    IncidentPage,
    ResolveResponse,
)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])
logger = logging.getLogger(__name__)


@router.get("", response_model=IncidentPage)
async def list_incidents(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> IncidentPage:
    """List stadium incidents in a paginated format.

    Allows filtering by status ('open', 'in_progress', 'resolved').
    Ordered by severity score (highest first) and creation date.

    Args:
        db: Database session.
        _: Authenticated user.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status_filter: Optional status filter.

    Returns:
        IncidentPage containing items list and pagination metadata.

    """
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


@router.post(
    "",
    response_model=IncidentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ops_staff))],
)
async def create_incident(
    payload: IncidentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
) -> Incident:
    """Create a new stadium incident.

    Only permitted for ops_staff. Applies strict prompt injection and PII
    input validation filters on title and description.

    Args:
        payload: Incident creation parameters.
        db: Database session.
        current_user: Authenticated staff member.

    Returns:
        The created Incident object.

    """
    # Security filters on title and description
    check_prompt_injection(payload.title)
    check_prompt_injection(payload.description)
    check_pii_in_input(payload.title + " " + payload.description)

    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info("Created incident %d by user %s", incident.id, current_user.username)
    return incident


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Incident:
    """Retrieve details of a specific incident by its unique ID.

    Args:
        incident_id: The ID of the incident to retrieve.
        db: Database session.
        _: Authenticated user.

    Returns:
        The Incident object.

    Raises:
        NotFoundError: If the incident does not exist.

    """
    incident = db.get(Incident, incident_id)
    if not incident:
        raise NotFoundError("Incident", incident_id).to_http_exception()
    return incident


@router.post(
    "/{incident_id}/resolve",
    response_model=ResolveResponse,
    dependencies=[Depends(require_role(UserRole.ops_staff))],
)
@limiter.limit("20/minute")
async def resolve_incident(
    request: Request,
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
) -> ResolveResponse:
    """Resolve an incident using GenAI.

    Only permitted for ops_staff. Enforces transaction safety (rollback
    on AI or network failure). Tracks actions in an immutable audit log.

    Args:
        request: FastAPI request object (for rate limiting).
        incident_id: Incident ID to resolve.
        db: Database session.
        current_user: Authenticated staff member.

    Returns:
        ResolveResponse detailing resolution status and AI playbook results.

    Raises:
        NotFoundError: If the incident is not found.
        AlreadyResolvedError: If the incident is already resolved.
        ResolutionRollbackError: If resolution fails and has been rolled back.

    """
    incident = db.get(Incident, incident_id)
    if not incident:
        raise NotFoundError("Incident", incident_id).to_http_exception()
    if incident.status == IncidentStatus.resolved:
        raise AlreadyResolvedError(incident_id).to_http_exception()

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
        incident.resolved_at = datetime.now(UTC)

        # Update audit with result
        audit_row.detail = f"Resolved via AI. confidence={ai_result.get('confidence')}"
        db.commit()
        db.refresh(audit_row)

        logger.info("Resolved incident %d via AI", incident.id)
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
        logger.error("Failed to resolve incident %d: %s", incident_id, exc)
        raise ResolutionRollbackError(incident_id, str(exc)).to_http_exception()


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.ops_staff))],
)
async def delete_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete an incident. Only permitted for ops_staff.

    Args:
        incident_id: Incident ID to delete.
        db: Database session.

    Raises:
        NotFoundError: If the incident does not exist.

    """
    incident = db.get(Incident, incident_id)
    if not incident:
        raise NotFoundError("Incident", incident_id).to_http_exception()
    db.delete(incident)
    db.commit()
    logger.info("Deleted incident %d", incident_id)
