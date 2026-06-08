from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self.cache: List[dict] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        for msg in self.cache[-50:]:
            await ws.send_json(msg)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        self.cache.append(message)
        if len(self.cache) > 200:
            self.cache = self.cache[-200:]
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
