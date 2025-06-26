from fastapi import WebSocket
from typing import Dict, List, Any
import json

class ConnectionManager:
    def __init__(self):
        # Map of stream_id to list of connected websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Map of stream_id to viewer count
        self.viewer_counts: Dict[int, int] = {}

    async def connect(self, websocket: WebSocket, stream_id: int):
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = []
            self.viewer_counts[stream_id] = 0
        
        self.active_connections[stream_id].append(websocket)
        self.viewer_counts[stream_id] += 1
        
        # Notify all clients about the updated viewer count
        await self.broadcast_viewer_count(stream_id)

    def disconnect(self, websocket: WebSocket, stream_id: int):
        if stream_id in self.active_connections:
            if websocket in self.active_connections[stream_id]:
                self.active_connections[stream_id].remove(websocket)
                self.viewer_counts[stream_id] -= 1
                
                # Clean up empty streams
                if not self.active_connections[stream_id]:
                    del self.active_connections[stream_id]
                    del self.viewer_counts[stream_id]
                    return
                
                # Schedule broadcast of viewer count
                import asyncio
                asyncio.create_task(self.broadcast_viewer_count(stream_id))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, stream_id: int, message: Any):
        if stream_id in self.active_connections:
            for connection in self.active_connections[stream_id]:
                await connection.send_text(json.dumps(message))

    async def broadcast_viewer_count(self, stream_id: int):
        await self.broadcast(stream_id, {
            "type": "viewer_count",
            "count": self.viewer_counts[stream_id]
        })

    def get_viewer_count(self, stream_id: int) -> int:
        return self.viewer_counts.get(stream_id, 0)
