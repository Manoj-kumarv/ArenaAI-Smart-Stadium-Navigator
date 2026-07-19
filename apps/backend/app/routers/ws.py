"""WebSocket endpoint for live telemetry push."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import telemetry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    telemetry.register(websocket)
    logger.info("WS client connected. Total: %d", len(telemetry._connections))
    try:
        while True:
            # Keep connection alive; all data is server-push
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        telemetry.unregister(websocket)
        logger.info("WS client disconnected. Total: %d", len(telemetry._connections))
