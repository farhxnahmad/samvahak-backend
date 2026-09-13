"""
Simple in-memory WebSocket broadcast manager.

For a single-instance deployment (typical for an SIH MVP on Railway) this is
sufficient. If Samvahak is ever scaled to multiple backend instances, this
would need to be swapped for a Redis pub/sub backed manager instead — but the
broadcast() call signature used by routers would stay identical.
"""
import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: dict):
        message = json.dumps({"event": event_type, "data": payload})
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)
        for s in stale:
            self.disconnect(s)


# Single shared instance imported by routers that need to push live updates
manager = ConnectionManager()
