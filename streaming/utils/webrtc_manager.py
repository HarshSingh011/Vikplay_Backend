from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebRTCConnection:
    """Represents a WebRTC peer connection"""
    def __init__(self, websocket: WebSocket, user_id: int, role: str, stream_code: str):
        self.websocket = websocket
        self.user_id = user_id
        self.role = role  # 'broadcaster' or 'viewer'
        self.stream_code = stream_code
        self.connected_at = datetime.utcnow()
        self.peer_id = f"{role}_{user_id}_{stream_code}"

class WebRTCManager:
    """WebRTC manager for handling peer-to-peer connections"""

    def __init__(self):
        # stream_code -> broadcaster WebRTCConnection
        self.broadcasters: Dict[str, WebRTCConnection] = {}
        
        # stream_code -> set of viewer WebRTCConnections
        self.viewers: Dict[str, Set[WebRTCConnection]] = {}
        
        # websocket -> WebRTCConnection mapping for quick lookup
        self.connections: Dict[WebSocket, WebRTCConnection] = {}
        
        # user_id -> stream_code mapping to enforce one stream per user
        self.active_streams_by_user: Dict[int, str] = {}
        
        # stream_code -> peak viewer count (in-memory tracking)
        self.max_viewers: Dict[str, int] = {}

    async def connect_broadcaster(
        self, 
        websocket: WebSocket, 
        stream_code: str, 
        user_id: int,
        skip_accept: bool = False
    ) -> Dict[str, any]:
        """Connect a broadcaster to start streaming"""
        if not skip_accept:
            await websocket.accept()
        
        # Check if user already has an active stream
        if user_id in self.active_streams_by_user:
            existing = self.active_streams_by_user[user_id]
            if existing != stream_code:
                await websocket.close(code=4001, reason="User already has an active stream")
                return {
                    "success": False,
                    "error": "User already has an active stream. Only one stream per user is allowed."
                }
        
        # Check if stream already has a broadcaster
        if stream_code in self.broadcasters:
            await websocket.close(code=4002, reason="Stream already has an active broadcaster")
            return {
                "success": False,
                "error": "Stream already has an active broadcaster"
            }
        
        connection = WebRTCConnection(websocket, user_id, 'broadcaster', stream_code)
        self.broadcasters[stream_code] = connection
        self.connections[websocket] = connection
        self.active_streams_by_user[user_id] = stream_code
        
        logger.info(f"Broadcaster connected: user_id={user_id}, stream_code={stream_code}")
        
        # Notify all viewers that broadcaster is ready
        await self.broadcast_to_viewers(stream_code, {
            "type": "broadcaster_ready",
            "stream_code": stream_code
        })
        
        return {"success": True, "role": "broadcaster", "stream_code": stream_code}

    async def connect_viewer(
        self, 
        websocket: WebSocket, 
        stream_code: str, 
        user_id: int,
        skip_accept: bool = False
    ) -> Dict[str, any]:
        """Connect a viewer to watch a stream"""
        if not skip_accept:
            await websocket.accept()
        
        # Check if broadcaster is active
        if stream_code not in self.broadcasters:
            await websocket.send_json({
                "type": "error",
                "message": "Broadcaster not available for this stream"
            })
            return {
                "success": False,
                "error": "Broadcaster not available"
            }
        
        # Block the broadcaster/host from joining their own stream as a viewer
        broadcaster = self.broadcasters[stream_code]
        if broadcaster.user_id == user_id:
            await websocket.send_json({
                "type": "error",
                "message": "You cannot join your own stream as a viewer"
            })
            try:
                await websocket.close(code=4006, reason="Cannot join your own stream as a viewer")
            except Exception:
                pass
            return {
                "success": False,
                "error": "Host cannot join their own stream as a viewer"
            }
        
        connection = WebRTCConnection(websocket, user_id, 'viewer', stream_code)
        
        if stream_code not in self.viewers:
            self.viewers[stream_code] = set()
        
        self.viewers[stream_code].add(connection)
        self.connections[websocket] = connection
        
        # Track peak viewer count
        current_count = len(self.viewers[stream_code])
        if current_count > self.max_viewers.get(stream_code, 0):
            self.max_viewers[stream_code] = current_count
        
        logger.info(f"Viewer connected: user_id={user_id}, stream_code={stream_code}, total_viewers={current_count}, peak={self.max_viewers.get(stream_code, 0)}")
        
        # Notify viewer that they're connected
        await websocket.send_json({
            "type": "connected",
            "role": "viewer",
            "stream_code": stream_code,
            "viewer_id": user_id,
            "viewer_count": len(self.viewers[stream_code])
        })
        
        # Notify broadcaster about new viewer
        await self.send_to_broadcaster(stream_code, {
            "type": "new_viewer",
            "viewer_id": user_id
        })
        
        # Update broadcaster with new viewer count
        await self.send_to_broadcaster(stream_code, {
            "type": "viewer_count",
            "count": len(self.viewers[stream_code])
        })
        
        return {"success": True, "role": "viewer", "stream_code": stream_code}

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebRTC connection"""
        if websocket not in self.connections:
            return
        
        connection = self.connections[websocket]
        stream_code = connection.stream_code
        user_id = connection.user_id
        
        if connection.role == 'broadcaster':
            # Remove broadcaster
            if stream_code in self.broadcasters:
                del self.broadcasters[stream_code]
            
            # Remove from active streams
            if user_id in self.active_streams_by_user:
                del self.active_streams_by_user[user_id]
            
            # Notify all viewers that stream ended and close their connections
            if stream_code in self.viewers:
                for viewer in list(self.viewers[stream_code]):
                    try:
                        if viewer.websocket in self.connections:
                            asyncio.create_task(
                                self._notify_and_close_viewer(viewer)
                            )
                            del self.connections[viewer.websocket]
                    except Exception as e:
                        logger.error(f"Error notifying/closing viewer: {e}")
                
                del self.viewers[stream_code]
            
            # Clean up peak viewer tracking (caller should read it before disconnect)
            if stream_code in self.max_viewers:
                del self.max_viewers[stream_code]
            
            logger.info(f"Broadcaster disconnected: user_id={user_id}, stream_code={stream_code}")
        
        elif connection.role == 'viewer':
            # Remove viewer
            if stream_code in self.viewers:
                self.viewers[stream_code].discard(connection)
                
                asyncio.create_task(self.send_to_broadcaster(stream_code, {
                    "type": "viewer_left",
                    "viewer_id": user_id
                }))
                
                if not self.viewers[stream_code]:
                    del self.viewers[stream_code]
                else:
                    asyncio.create_task(self.send_to_broadcaster(stream_code, {
                        "type": "viewer_count",
                        "count": len(self.viewers[stream_code])
                    }))
            
            logger.info(f"Viewer disconnected: user_id={user_id}, stream_code={stream_code}")
        
        del self.connections[websocket]

    async def handle_signal(self, websocket: WebSocket, data: dict):
        """Handle WebRTC signaling messages"""
        if websocket not in self.connections:
            return
        
        connection = self.connections[websocket]
        stream_code = connection.stream_code
        signal_type = data.get("type")
        
        if connection.role == 'broadcaster':
            target_viewer_id = data.get("target")
            if signal_type in ['answer', 'ice_candidate']:
                await self.send_to_viewer(stream_code, target_viewer_id, data)
        
        elif connection.role == 'viewer':
            if signal_type in ['offer', 'ice_candidate']:
                data['source'] = connection.peer_id
                await self.send_to_broadcaster(stream_code, data)

    async def send_to_broadcaster(self, stream_code: str, message: dict):
        """Send a message to the broadcaster of a stream"""
        if stream_code not in self.broadcasters:
            return
        
        broadcaster = self.broadcasters[stream_code]
        try:
            await broadcaster.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to broadcaster: {e}")
            self.disconnect(broadcaster.websocket)

    async def send_to_viewer(self, stream_code: str, user_id: int, message: dict):
        """Send a message to a specific viewer by user_id"""
        if stream_code not in self.viewers:
            logger.warning(f"No viewers for stream {stream_code}")
            return
        
        for viewer in self.viewers[stream_code]:
            if viewer.user_id == user_id:
                try:
                    await viewer.websocket.send_json(message)
                    logger.info(f"Sent message to viewer user_id={user_id}, type={message.get('type')}")
                except Exception as e:
                    logger.error(f"Error sending to viewer: {e}")
                    self.disconnect(viewer.websocket)
                return
        
        logger.warning(f"Viewer user_id={user_id} not found in stream {stream_code}")

    async def broadcast_to_viewers(self, stream_code: str, message: dict):
        """Broadcast a message to all viewers of a stream"""
        if stream_code not in self.viewers:
            return
        
        disconnected = set()
        for viewer in self.viewers[stream_code]:
            try:
                await viewer.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to viewer: {e}")
                disconnected.add(viewer)
        
        for viewer in disconnected:
            self.disconnect(viewer.websocket)

    async def broadcast_chat_message(self, stream_code: str, user_id: int, username: str, message: str, role: str = "viewer"):
        """Broadcast a chat message to everyone in the stream"""
        chat_data = {
            "type": "chat_message",
            "stream_code": stream_code,
            "user_id": user_id,
            "username": username,
            "message": message,
            "role": role,
            "timestamp": datetime.utcnow().isoformat()
        }

        if stream_code in self.broadcasters:
            try:
                await self.broadcasters[stream_code].websocket.send_json(chat_data)
            except Exception as e:
                logger.error(f"Error sending chat to broadcaster: {e}")

        if stream_code in self.viewers:
            disconnected = set()
            for viewer in self.viewers[stream_code]:
                try:
                    await viewer.websocket.send_json(chat_data)
                except Exception as e:
                    logger.error(f"Error sending chat to viewer: {e}")
                    disconnected.add(viewer)
            for viewer in disconnected:
                self.disconnect(viewer.websocket)

    async def relay_sync_timestamp(self, stream_code: str, broadcaster_ts: float):
        """Relay broadcaster's sync timestamp to all viewers"""
        sync_data = {
            "type": "sync_timestamp",
            "stream_code": stream_code,
            "broadcaster_ts": broadcaster_ts,
            "server_ts": datetime.utcnow().timestamp()
        }
        await self.broadcast_to_viewers(stream_code, sync_data)

    async def request_go_live(self, stream_code: str, viewer_id: int):
        """Viewer requests to jump to live"""
        if stream_code in self.broadcasters:
            await self.send_to_broadcaster(stream_code, {
                "type": "keyframe_request",
                "viewer_id": viewer_id
            })
            logger.info(f"Keyframe requested by viewer {viewer_id} for stream {stream_code}")

    async def _notify_and_close_viewer(self, viewer: WebRTCConnection):
        """Send stream-ended notification to a viewer and close their WebSocket"""
        try:
            await viewer.websocket.send_json({
                "type": "stream_ended",
                "message": "The broadcaster has stopped streaming. Stream is now closed."
            })
        except Exception as e:
            logger.error(f"Error sending stream_ended to viewer {viewer.user_id}: {e}")
        try:
            await viewer.websocket.close(code=4007, reason="Broadcaster stopped streaming")
        except Exception as e:
            logger.error(f"Error closing viewer websocket {viewer.user_id}: {e}")

    def get_viewer_count(self, stream_code: str) -> int:
        """Get the number of viewers for a stream"""
        return len(self.viewers.get(stream_code, set()))

    def get_max_viewer_count(self, stream_code: str) -> int:
        """Get the peak viewer count for a stream"""
        return self.max_viewers.get(stream_code, 0)

    def is_user_streaming(self, user_id: int) -> Optional[str]:
        """Check if a user is currently streaming, returns stream_code if yes"""
        return self.active_streams_by_user.get(user_id)

    def get_active_streams(self) -> Dict[str, dict]:
        """Get all active streams with their details"""
        return {
            stream_code: {
                "stream_code": stream_code,
                "broadcaster_id": broadcaster.user_id,
                "viewer_count": self.get_viewer_count(stream_code),
                "started_at": broadcaster.connected_at.isoformat()
            }
            for stream_code, broadcaster in self.broadcasters.items()
        }

# Import asyncio for async tasks
import asyncio

# Global WebRTC manager instance
webrtc_manager = WebRTCManager()
