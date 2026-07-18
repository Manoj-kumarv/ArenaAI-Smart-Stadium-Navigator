from __future__ import annotations

import asyncio
import logging
import pytest
from unittest.mock import MagicMock, patch
from fastapi import status
from jose import jwt

from app.auth import verify_password, get_current_user, get_password_hash, create_access_token, create_refresh_token
from app.ai.fallback import _classify_query, _classify_incident_severity
from app.ai.crowd_agent import _validate as validate_crowd
from app.ai.fan_agent import _validate as validate_fan
from app.ai.incident_agent import _validate as validate_incident
from app.middleware.correlation import get_correlation_id
from app.logging_config import StructuredFormatter, setup_logging
from app.models import User, UserRole, Incident, IncidentStatus, Zone
from app.telemetry import telemetry_loop
from app.config import settings
from tests.conftest import ops_headers, fan_headers


# ─── Part 1: Request Size Middleware ──────────────────────────────────────────

def test_request_size_middleware_large_body(client):
    headers = {"Content-Length": "10000000"}  # 10MB, way above 1MB limit
    res = client.post("/api/auth/signup", json={"username": "a"}, headers=headers)
    assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_request_size_middleware_invalid_length(client):
    headers = {"Content-Length": "not-an-integer"}
    res = client.post("/api/auth/signup", json={"username": "a"}, headers=headers)
    assert res.status_code != status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


# ─── Part 2: Fallback Classifications ─────────────────────────────────────────

def test_fallback_classify_query():
    assert _classify_query("Give me food please") == "food"
    assert _classify_query("I need a doctor") == "medical"
    assert _classify_query("Show me a toilet") == "toilets"
    assert _classify_query("hello") == "default"


def test_fallback_classify_incident_severity():
    assert _classify_incident_severity("medical emergency", "help") == "critical"
    assert _classify_incident_severity("crowd", "fight breaking out") == "high"
    assert _classify_incident_severity("spill", "water spill on section") == "medium"
    assert _classify_incident_severity("info", "just testing") == "low"


# ─── Part 3: Client and Agent Validation ──────────────────────────────────────

@patch("app.ai.gemini_client.genai")
def test_ensure_client_configures(mock_genai):
    from app.ai.gemini_client import _ensure_client
    with patch("app.ai.gemini_client.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key-value"
        import app.ai.gemini_client
        app.ai.gemini_client._client_initialized = False
        assert _ensure_client() is True
        mock_genai.configure.assert_called_once_with(api_key="test-key-value")


@patch("app.ai.gemini_client.genai")
def test_ensure_client_failure_logs(mock_genai):
    from app.ai.gemini_client import _ensure_client
    mock_genai.configure.side_effect = Exception("Config error")
    with patch("app.ai.gemini_client.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key-value"
        import app.ai.gemini_client
        app.ai.gemini_client._client_initialized = False
        assert _ensure_client() is False


def test_validation_crowd():
    assert validate_crowd(None, "zone_1") is False
    assert validate_crowd({"zone_id": "zone_1"}, "zone_1") is False
    assert validate_crowd({"zone_id": "zone_1", "cause": "c", "recommendation": "r", "confidence": "invalid"}, "zone_1") is False


def test_validation_fan():
    assert validate_fan(None) is False
    assert validate_fan({"answer_en": "a"}) is False
    assert validate_fan({"answer_en": "a", "answer_es": "b", "answer_ar": "c", "confidence": "invalid"}) is False


def test_validation_incident():
    assert validate_incident(None, "zone_1") is False
    assert validate_incident({"zone_id": "zone_1"}, "zone_1") is False
    assert validate_incident({"zone_id": "zone_1", "severity": "invalid", "confidence": 0.5, "cause": "c", "recommendation": "r"}, "zone_1") is False
    assert validate_incident({"zone_id": "zone_1", "severity": "low", "confidence": "invalid", "cause": "c", "recommendation": "r"}, "zone_1") is False


@pytest.mark.asyncio
async def test_call_gemini_none():
    from app.ai.gemini_client import call_gemini, call_gemini_json
    with patch("app.ai.gemini_client._ensure_client", return_value=False):
        assert await call_gemini("test") is None
        assert await call_gemini_json("test") is None


# ─── Part 4: Authentication Core ──────────────────────────────────────────────

def test_verify_password_exception():
    assert verify_password(None, "hash") is False


def test_get_current_user_jwt_exceptions(db):
    with pytest.raises(Exception):
        get_current_user("invalid.token.here", db)


def test_get_current_user_no_sub(db):
    token = jwt.encode({"role": "fan"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(Exception):
        get_current_user(token, db)


def test_get_current_user_missing_or_inactive(db):
    token_missing = create_access_token(9999, "fan")
    with pytest.raises(Exception):
        get_current_user(token_missing, db)
    
    inactive_user = User(
        username="inactive_u",
        email="inactive@test.local",
        hashed_password="...",
        role=UserRole.fan,
        is_active=False
    )
    db.add(inactive_user)
    db.commit()
    token_inactive = create_access_token(inactive_user.id, "fan")
    with pytest.raises(Exception):
        get_current_user(token_inactive, db)


# ─── Part 5: Correlation ──────────────────────────────────────────────────────

def test_correlation_id_outside_context():
    assert get_correlation_id() is None


# ─── Part 6: Structured Logging Formatter ─────────────────────────────────────

def test_structured_formatter():
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="path/to/file.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    assert "Test message" in formatted

    try:
        raise ValueError("Oops")
    except ValueError as exc:
        import sys
        record.exc_info = sys.exc_info()
    formatted_exc = formatter.format(record)
    assert "ValueError: Oops" in formatted_exc

    record.user_id = 42
    record.request_path = "/test"
    record.request_method = "GET"
    record.status_code = 200
    formatted_extra = formatter.format(record)
    assert '"user_id": 42' in formatted_extra
    assert '"request_path": "/test"' in formatted_extra


def test_setup_logging_structured():
    setup_logging(level="DEBUG", structured=True)
    setup_logging(level="INFO", structured=False)


# ─── Part 7: Auth Router ──────────────────────────────────────────────────────

def test_login_inactive_user(client, db):
    inactive = User(
        username="inactive_ops",
        email="inactive_ops@test.local",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ops_staff,
        is_active=False
    )
    db.add(inactive)
    db.commit()
    res = client.post("/api/auth/login", json={"username": "inactive_ops", "password": "password123"})
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_refresh_token_invalid_type(client, db):
    wrong_token = create_access_token(1, "fan")
    res = client.post("/api/auth/refresh", json={"refresh_token": wrong_token})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_token_inactive_user(client, db):
    inactive = User(
        username="inactive_refresh",
        email="inactive_refresh@test.local",
        hashed_password=get_password_hash("password123"),
        role=UserRole.fan,
        is_active=False
    )
    db.add(inactive)
    db.commit()
    ref_token = create_refresh_token(inactive.id)
    res = client.post("/api/auth/refresh", json={"refresh_token": ref_token})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Part 8: Broadcast Router ─────────────────────────────────────────────────

def test_broadcast_incident_not_found(client):
    res = client.post("/api/broadcast", json={"incident_id": 99999}, headers=ops_headers(client))
    assert res.status_code == status.HTTP_404_NOT_FOUND


@patch("app.routers.broadcast.generate_broadcast")
def test_broadcast_atomicity_error(mock_gen, client, db):
    inc = Incident(title="T", description="D", status=IncidentStatus.open)
    db.add(inc)
    db.commit()
    
    mock_gen.return_value = {"message_en": "", "message_es": "Spanish", "message_ar": "Arabic"}
    res = client.post("/api/broadcast", json={"incident_id": inc.id}, headers=ops_headers(client))
    assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Broadcast generation failed" in res.json()["detail"]


def test_list_broadcasts(client):
    res = client.get("/api/broadcast", headers=fan_headers(client))
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.json(), list)


def test_list_audit_log_pagination(client):
    res = client.get("/api/broadcast/audit?page=1&page_size=5", headers=ops_headers(client))
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 5


# ─── Part 9: Fan Router ───────────────────────────────────────────────────────

@patch("app.routers.fan.orchestrate_fan")
def test_ask_fan_assistant(mock_orch, client):
    mock_orch.return_value = {"answer_en": "Yes", "answer_es": "Si", "answer_ar": "Naam", "confidence": 0.9, "used_ai": True}
    res = client.post("/api/fan/ask", json={"query": "Where is Gate A?"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["answer_en"] == "Yes"


# ─── Part 10: Incidents Router ────────────────────────────────────────────────

def test_list_incidents_filter(client):
    res = client.get("/api/incidents?status=open&page=1&page_size=10", headers=ops_headers(client))
    assert res.status_code == status.HTTP_200_OK
    assert "items" in res.json()


def test_get_incident_not_found(client):
    res = client.get("/api/incidents/99999", headers=ops_headers(client))
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_get_incident_success(client, db):
    inc = Incident(title="T", description="D", status=IncidentStatus.open)
    db.add(inc)
    db.commit()
    res = client.get(f"/api/incidents/{inc.id}", headers=ops_headers(client))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["title"] == "T"


def test_resolve_incident_not_found(client):
    res = client.post("/api/incidents/99999/resolve", headers=ops_headers(client))
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_incident_not_found(client):
    res = client.delete("/api/incidents/99999", headers=ops_headers(client))
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_incident_success(client, db):
    inc = Incident(title="T", description="D", status=IncidentStatus.open)
    db.add(inc)
    db.commit()
    res = client.delete(f"/api/incidents/{inc.id}", headers=ops_headers(client))
    assert res.status_code == status.HTTP_204_NO_CONTENT


# ─── Part 11: Zones Router ────────────────────────────────────────────────────

def test_zones_exceptions(client):
    res = client.get("/api/zones/invalid_zone")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    res = client.post("/api/zones/invalid_zone/analyse", headers=ops_headers(client))
    assert res.status_code == status.HTTP_404_NOT_FOUND
    res = client.post("/api/zones/action", json={"zone_id": "invalid_zone", "action": "deploy_volunteers", "detail": "test"}, headers=ops_headers(client))
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_get_zone_success(client, db):
    zone = Zone(id="test_zone", name="Test Zone", zone_type="gate", capacity=100, density_pct=0.1, color_state="green")
    db.add(zone)
    db.commit()
    res = client.get(f"/api/zones/{zone.id}")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["name"] == "Test Zone"


# ─── Part 12: Schemas & PII ───────────────────────────────────────────────────

def test_schema_validate_action_exception():
    from app.schemas import ZoneActionRequest
    with pytest.raises(Exception):
        ZoneActionRequest(zone_id="1", action="invalid")


def test_pii_filters_ssn_and_card():
    from app.ai.filters import check_pii_in_input
    with pytest.raises(Exception):
        check_pii_in_input("my SSN is 123-45-6789")
    with pytest.raises(Exception):
        check_pii_in_input("card number 1234-5678-9012-3456")


# ─── Part 13: Readiness Check Database Exception ──────────────────────────────

@patch("app.main.get_db")
def test_readiness_db_exception(mock_get_db, client):
    mock_get_db.side_effect = Exception("DB Connection Failed")
    res = client.get("/ready")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "degraded"
    assert "error" in res.json()["checks"]["database"]


# ─── Part 14: Telemetry Loop Cleanup and Exceptions ──────────────────────────

@pytest.mark.asyncio
async def test_telemetry_loop_exceptions_and_cleanup(db):
    mock_db = MagicMock()
    mock_zone = MagicMock(spec=Zone)
    mock_zone.id = "gate_a"
    mock_zone.zone_type.value = "gate"
    mock_db.query.return_value.all.side_effect = [[mock_zone], Exception("Loop database error")]
    
    def mock_db_fn():
        yield mock_db
    
    with patch("app.telemetry.TELEMETRY_STARTUP_DELAY_SECONDS", 0.001):
        with patch("app.telemetry.TELEMETRY_INTERVAL_MIN_SECONDS", 0.001):
            with patch("app.telemetry.TELEMETRY_INTERVAL_MAX_SECONDS", 0.002):
                task = asyncio.create_task(telemetry_loop(mock_db_fn))
                await asyncio.sleep(0.3)
                task.cancel()
                try:
                    await task
                except (Exception, asyncio.CancelledError):
                    pass


@pytest.mark.asyncio
async def test_telemetry_loop_successful_cleanup(db):
    zone_a = Zone(id="gate_a", name="Gate A", zone_type="gate", capacity=1000, density_pct=0.5, color_state="green")
    db.add(zone_a)
    db.commit()

    def dummy_db_fn():
        yield db

    with patch("app.telemetry.TELEMETRY_STARTUP_DELAY_SECONDS", 0.001):
        with patch("app.telemetry.TELEMETRY_INTERVAL_MIN_SECONDS", 0.001):
            with patch("app.telemetry.TELEMETRY_INTERVAL_MAX_SECONDS", 0.002):
                with patch("app.telemetry.TELEMETRY_CLEANUP_INTERVAL_SECONDS", -1):
                    task = asyncio.create_task(telemetry_loop(dummy_db_fn))
                    await asyncio.sleep(0.3)
                    task.cancel()
                    try:
                        await task
                    except (Exception, asyncio.CancelledError):
                        pass
