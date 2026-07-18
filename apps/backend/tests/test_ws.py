"""Unit tests for the WebSocket telemetry endpoint.
Provides 100% test coverage for app/routers/ws.py.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import WebSocketDisconnect

from app.routers.ws import telemetry_ws


@pytest.mark.asyncio
async def test_telemetry_ws_lifecycle():
    """Verify WebSocket endpoint lifecycle: accept, register, receive, disconnect, unregister."""
    mock_ws = AsyncMock()
    # Simulate a receive_text that raises WebSocketDisconnect on first call to break the keep-alive loop
    mock_ws.receive_text.side_effect = WebSocketDisconnect()

    with patch("app.telemetry.register") as mock_reg, \
         patch("app.telemetry.unregister") as mock_unreg:

        await telemetry_ws(mock_ws)

        mock_ws.accept.assert_called_once()
        mock_reg.assert_called_once_with(mock_ws)
        mock_ws.receive_text.assert_called_once()
        mock_unreg.assert_called_once_with(mock_ws)
