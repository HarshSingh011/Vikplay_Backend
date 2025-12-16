from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import logging

logger = logging.getLogger(__name__)

class StreamWebSocketManager:
    """WebSocket manager for real-time streaming features"""

    def __init__(self):
        # stream_id -> set of active connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # stream_id -> list of recent chat messages
        self.recent_messages: Dict[int, List[dict]] = {}

    async def connect(self, websocket: WebSocket, stream_id: int):
        """Connect a WebSocket to a stream"""
        await websocket.accept()

        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = set()
            self.recent_messages[stream_id] = []

        self.active_connections[stream_id].add(websocket)
        logger.info(f"WebSocket connected to stream {stream_id}. Total connections: {len(self.active_connections[stream_id])}")

    def disconnect(self, websocket: WebSocket, stream_id: int):
        """Disconnect a WebSocket from a stream"""
        if stream_id in self.active_connections:
            self.active_connections[stream_id].discard(websocket)
            if not self.active_connections[stream_id]:
                del self.active_connections[stream_id]
                del self.recent_messages[stream_id]
            logger.info(f"WebSocket disconnected from stream {stream_id}")

    async def broadcast_to_stream(self, stream_id: int, message: dict):
        """Broadcast a message to all connections in a stream"""
        if stream_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[stream_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, stream_id)

    async def broadcast_chat_message(self, stream_id: int, chat_message: dict):
        """Broadcast a chat message and keep recent messages"""
        # Add to recent messages (keep last 50)
        if stream_id not in self.recent_messages:
            self.recent_messages[stream_id] = []

        self.recent_messages[stream_id].append(chat_message)
        if len(self.recent_messages[stream_id]) > 50:
            self.recent_messages[stream_id].pop(0)

        # Broadcast to all connections
        await self.broadcast_to_stream(stream_id, {
            "type": "chat_message",
            "data": chat_message
        })

    async def broadcast_stream_status(self, stream_id: int, is_live: bool, viewer_count: int = 0):
        """Broadcast stream status updates"""
        await self.broadcast_to_stream(stream_id, {
            "type": "stream_status",
            "data": {
                "stream_id": stream_id,
                "is_live": is_live,
                "viewer_count": viewer_count
            }
        })

    def get_recent_messages(self, stream_id: int) -> List[dict]:
        """Get recent chat messages for a stream"""
        return self.recent_messages.get(stream_id, [])

    def get_connection_count(self, stream_id: int) -> int:
        """Get number of active connections for a stream"""
        return len(self.active_connections.get(stream_id, set()))

# Global WebSocket manager instance
stream_ws_manager = StreamWebSocketManager()