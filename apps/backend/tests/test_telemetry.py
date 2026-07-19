"""Unit tests for the telemetry simulation loop and WebSocket broadcaster.
Provides 100% test coverage for app/telemetry.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import ColorState, Zone, ZoneType
from app.telemetry import (
    _broadcast,
    _connections,
    _init_bases,
    _step_density,
    _zone_bases,
    register,
    telemetry_loop,
    unregister,
)


def test_ws_register_unregister():
    """Verify that WS sockets are registered and unregistered correctly."""
    mock_ws = MagicMock()

    register(mock_ws)
    assert mock_ws in _connections

    unregister(mock_ws)
    assert mock_ws not in _connections


@pytest.mark.asyncio
async def test_broadcast_success_and_failure():
    """Verify broadcast sends data and unregisters dead sockets on exception."""
    mock_ws_success = AsyncMock()
    mock_ws_fail = AsyncMock()
    mock_ws_fail.send_text.side_effect = ValueError("Dead socket connection")

    register(mock_ws_success)
    register(mock_ws_fail)

    await _broadcast({"test": "data"})

    # Assert successful socket got call
    mock_ws_success.send_text.assert_called_once()

    # Assert dead socket got discarded
    assert mock_ws_fail not in _connections
    assert mock_ws_success in _connections

    # Clean up
    unregister(mock_ws_success)


def test_step_density_and_bases():
    """Verify zone base initialization and random walk step density generation."""
    mock_zone_hot = Zone(id="gate_a", name="Gate A", zone_type=ZoneType.gate, capacity=2000, density_pct=0.5)
    mock_zone_cold = Zone(id="med_a", name="Med A", zone_type=ZoneType.medical, capacity=100, density_pct=0.1)
    mock_zone_norm = Zone(id="sec_a", name="Sec A", zone_type=ZoneType.section, capacity=1000, density_pct=0.3)

    _init_bases([mock_zone_hot, mock_zone_cold, mock_zone_norm])

    assert "gate_a" in _zone_bases
    assert 0.55 <= _zone_bases["gate_a"] <= 0.80
    assert 0.05 <= _zone_bases["med_a"] <= 0.20
    assert 0.20 <= _zone_bases["sec_a"] <= 0.60

    # Run random walk step
    new_density = _step_density("gate_a", 0.5)
    assert 0.0 <= new_density <= 1.05


class TelemetryExitException(Exception):
    """Exception to exit the telemetry infinite loop for test purposes."""

    pass


@pytest.mark.asyncio
async def test_telemetry_loop():
    """Verify database initialization and one step execution of the telemetry loop."""
    mock_zone = Zone(
        id="gate_a",
        name="Gate A",
        zone_type=ZoneType.gate,
        capacity=2000,
        density_pct=0.5,
        color_state=ColorState.green,
    )

    # Setup mock DB query
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = [mock_zone]

    def mock_get_db():
        yield mock_db

    # Mock sleep to:
    # First sleep (startup delay) -> pass
    # Second sleep (interval loop) -> raise TelemetryExitException to break out
    sleep_calls = []

    async def mock_sleep(secs):
        sleep_calls.append(secs)
        if len(sleep_calls) > 2:
            raise TelemetryExitException()

    with (
        patch("asyncio.sleep", mock_sleep),
        patch("app.telemetry._broadcast", new_callable=AsyncMock) as mock_broadcast,
    ):
        with pytest.raises(TelemetryExitException):
            await telemetry_loop(mock_get_db)

        assert len(sleep_calls) == 3
        mock_db.query.assert_called()
        mock_db.commit.assert_called_once()
        mock_broadcast.assert_called_once()
