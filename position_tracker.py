from fastapi import WebSocket
from typing import Dict
import asyncio

class PositionTracker:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.current_positions: Dict[str, tuple] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self.current_positions.pop(client_id, None)
        print(f"Client {client_id} disconnected")

    async def update_position(self, client_id: str, latitude: float, longitude: float):
        self.current_positions[client_id] = (latitude, longitude)
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": "position_update",
                "latitude": latitude,
                "longitude": longitude
            })

    def get_current_position(self, client_id: str) -> tuple:
        return self.current_positions.get(client_id, None)