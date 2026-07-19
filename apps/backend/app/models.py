from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base

# ─── Enums ────────────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    ops_staff = "ops_staff"
    fan = "fan"


class ZoneType(str, enum.Enum):
    gate = "gate"
    section = "section"
    concourse = "concourse"
    parking = "parking"
    medical = "medical"
    volunteer_post = "volunteer_post"


class ColorState(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"
    critical = "critical"


class IncidentStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"


class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AuditAction(str, enum.Enum):
    incident_resolve = "incident_resolve"
    broadcast_send = "broadcast_send"
    volunteer_deploy = "volunteer_deploy"
    signage_update = "signage_update"
    zone_action = "zone_action"


# ─── Zone color-state logic (canonical — also used in tests) ──────────────────


def density_to_color(density_pct: float) -> ColorState:
    """Property 1 (tested):
    green    : density_pct < 0.60
    yellow   : 0.60 <= density_pct < 0.85
    red      : 0.85 <= density_pct < 0.95
    critical : density_pct >= 0.95
    """
    if density_pct < 0.60:
        return ColorState.green
    elif density_pct < 0.85:
        return ColorState.yellow
    elif density_pct < 0.95:
        return ColorState.red
    else:
        return ColorState.critical


def cap_density(density_pct: float) -> tuple[float, bool]:
    """Property 2: cap at 1.0, return (capped_value, was_capped)."""
    if density_pct > 1.0:
        return 1.0, True
    return density_pct, False


# ─── Models ───────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.fan)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    audit_logs = relationship("AuditLog", back_populates="user")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(32), primary_key=True)  # e.g. "gate_a", "section_101"
    name = Column(String(128), nullable=False)
    zone_type = Column(Enum(ZoneType), nullable=False)
    capacity = Column(Integer, nullable=False, default=500)
    density_pct = Column(Float, nullable=False, default=0.0)
    color_state = Column(Enum(ColorState), nullable=False, default=ColorState.green)
    is_step_free = Column(Boolean, default=False)
    is_low_noise = Column(Boolean, default=False)
    x = Column(Float, nullable=False, default=0.0)  # SVG coordinate
    y = Column(Float, nullable=False, default=0.0)
    w = Column(Float, nullable=False, default=60.0)
    h = Column(Float, nullable=False, default=40.0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    density_history = relationship("ZoneDensityHistory", back_populates="zone")


class ZoneDensityHistory(Base):
    __tablename__ = "zone_density_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(32), ForeignKey("zones.id"), nullable=False, index=True)
    density_pct = Column(Float, nullable=False)
    color_state = Column(Enum(ColorState), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now())

    zone = relationship("Zone", back_populates="density_history")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(32), ForeignKey("zones.id"), nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.medium)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.open)
    ai_severity_score = Column(Float, nullable=True)  # 0.0–1.0 from AI agent
    ai_resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime, nullable=True)

    zone = relationship("Zone")
    audit_logs = relationship("AuditLog", back_populates="incident")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(Enum(AuditAction), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    zone_id = Column(String(32), nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
    incident = relationship("Incident", back_populates="audit_logs")


class BroadcastLog(Base):
    __tablename__ = "broadcast_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    message_en = Column(Text, nullable=False)
    message_es = Column(Text, nullable=False)
    message_ar = Column(Text, nullable=False)
    used_ai = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
