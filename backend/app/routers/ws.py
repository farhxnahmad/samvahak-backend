from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Single broadcast channel for live dashboard updates: vehicle_update,
    shipment_created, shipment_update, incident_new, incident_update,
    citizen_report_new, citizen_report_update, weather_update.

    This stream is read-only situational-awareness data (the same info shown
    on the public dashboard/map), so it's left open without auth for MVP
    simplicity. Frontend usage:

        const ws = new WebSocket("wss://<api-host>/api/ws");
        ws.onmessage = (e) => {
          const { event, data } = JSON.parse(e.data);
          // dispatch on `event` to update the right slice of dashboard state
        };
    """
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect incoming client messages on this channel, but we
            # must keep receiving (or the connection is considered idle/closed
            # by some proxies) — this also lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
