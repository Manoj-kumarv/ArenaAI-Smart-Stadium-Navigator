"""Pydantic v2 request/response schemas for all endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import ColorState, IncidentSeverity, IncidentStatus, UserRole, ZoneType, AuditAction


# ─── Auth ─────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.fan


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── Zone ─────────────────────────────────────────────────────────────────────

class ZoneOut(BaseModel):
    id: str
    name: str
    zone_type: ZoneType
    capacity: int
    density_pct: float
    color_state: ColorState
    is_step_free: bool
    is_low_noise: bool
    x: float
    y: float
    w: float
    h: float
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ZoneActionRequest(BaseModel):
    zone_id: str
    action: str = Field(description="broadcast | deploy_volunteers | update_signage")
    detail: Optional[str] = Field(default=None, max_length=512)

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"broadcast", "deploy_volunteers", "update_signage"}
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v


class CrowdAnalysisResponse(BaseModel):
    zone_id: str
    cause: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    used_ai: bool


# ─── Incident ─────────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    zone_id: Optional[str] = None
    title: str = Field(min_length=5, max_length=256)
    description: str = Field(min_length=10, max_length=2000)
    severity: IncidentSeverity = IncidentSeverity.medium


class IncidentOut(BaseModel):
    id: int
    zone_id: Optional[str] = None
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    ai_severity_score: Optional[float] = None
    ai_resolution: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IncidentPage(BaseModel):
    items: list[IncidentOut]
    total: int
    page: int
    page_size: int


class ResolveResponse(BaseModel):
    incident_id: int
    status: IncidentStatus
    ai_result: dict
    audit_id: int


# ─── Broadcast ────────────────────────────────────────────────────────────────

class BroadcastRequest(BaseModel):
    incident_id: int


class BroadcastOut(BaseModel):
    id: int
    incident_id: Optional[int] = None
    message_en: str
    message_es: str
    message_ar: str
    used_ai: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Fan ─────────────────────────────────────────────────────────────────────

class FanQueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)


class FanQueryResponse(BaseModel):
    answer_en: str
    answer_es: str
    answer_ar: str
    confidence: float = Field(ge=0.0, le=1.0)
    used_ai: bool


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    action: AuditAction
    user_id: Optional[int] = None
    incident_id: Optional[int] = None
    zone_id: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditPage(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


# ─── KPI Dashboard ────────────────────────────────────────────────────────────

class KPIResponse(BaseModel):
    attendance: int
    active_incidents: int
    avg_wait_minutes: float
    ai_actions_taken: int
    critical_zones: int
