"""Alert listing + live WebSocket stream."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.models.schemas import AlertItem
from app.services.events_hub import get_event_hub
from app.services.firebase_client import get_firebase_service

log = get_logger("api.alerts")
router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertItem])
async def list_alerts(limit: int = 50) -> list[AlertItem]:
    data = get_firebase_service().list_alerts(limit)
    return [AlertItem(**{k: a.get(k) for k in AlertItem.model_fields}) for a in data]


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket) -> None:
    """Push live alerts to the dashboard as JSON messages."""
    await websocket.accept()
    hub = get_event_hub()
    queue = await hub.subscribe()
    await websocket.send_json({"type": "hello", "data": {"connected": True}})
    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(msg)
            except asyncio.TimeoutError:
                # Heartbeat keeps proxies from closing an idle socket.
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception as e:  # noqa: BLE001  # pragma: no cover
        log.warning("ws.error", extra={"error": str(e)})
    finally:
        hub.unsubscribe(queue)
