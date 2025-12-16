from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebRTCConnection:
    """Represents a WebRTC peer connection"""
    def __init__(self, websocket: WebSocket, user_id: int, role: str, stream_id: int):
        self.websocket = websocket
        self.user_id = user_id
        self.role = role  # 'broadcaster' or 'viewer'
        self.stream_id = stream_id
        self.connected_at = datetime.utcnow()
        self.peer_id = f"{role}_{user_id}_{stream_id}"

class WebRTCManager:
    """WebRTC manager for handling peer-to-peer connections"""

    def __init__(self):
        # stream_id -> broadcaster WebRTCConnection
        self.broadcasters: Dict[int, WebRTCConnection] = {}
        
        # stream_id -> set of viewer WebRTCConnections
        self.viewers: Dict[int, Set[WebRTCConnection]] = {}
        
        # websocket -> WebRTCConnection mapping for quick lookup
        self.connections: Dict[WebSocket, WebRTCConnection] = {}
        
        # user_id -> stream_id mapping to enforce one stream per user
        self.active_streams_by_user: Dict[int, int] = {}

    async def connect_broadcaster(
        self, 
        websocket: WebSocket, 
        stream_id: int, 
        user_id: int
    ) -> Dict[str, any]:
        """Connect a broadcaster to start streaming"""
        await websocket.accept()
        
        # Check if user already has an active stream
        if user_id in self.active_streams_by_user:
            existing_stream_id = self.active_streams_by_user[user_id]
            if existing_stream_id != stream_id:
                await websocket.close(code=4001, reason="User already has an active stream")
                return {
                    "success": False,
                    "error": "User already has an active stream. Only one stream per user is allowed."
                }
        
        # Check if stream already has a broadcaster
        if stream_id in self.broadcasters:
            await websocket.close(code=4002, reason="Stream already has an active broadcaster")
            return {
                "success": False,
                "error": "Stream already has an active broadcaster"
            }
        
        connection = WebRTCConnection(websocket, user_id, 'broadcaster', stream_id)
        self.broadcasters[stream_id] = connection
        self.connections[websocket] = connection
        self.active_streams_by_user[user_id] = stream_id
        
        logger.info(f"Broadcaster connected: user_id={user_id}, stream_id={stream_id}")
        
        # Notify all viewers that broadcaster is ready
        await self.broadcast_to_viewers(stream_id, {
            "type": "broadcaster_ready",
            "stream_id": stream_id
        })
        
        return {"success": True, "role": "broadcaster", "stream_id": stream_id}

    async def connect_viewer(
        self, 
        websocket: WebSocket, 
        stream_id: int, 
        user_id: int
    ) -> Dict[str, any]:
        """Connect a viewer to watch a stream"""
        await websocket.accept()
        
        # Check if broadcaster is active
        if stream_id not in self.broadcasters:
            await websocket.send_json({
                "type": "error",
                "message": "Broadcaster not available for this stream"
            })
            return {
                "success": False,
                "error": "Broadcaster not available"
            }
        
        connection = WebRTCConnection(websocket, user_id, 'viewer', stream_id)
        
        if stream_id not in self.viewers:
            self.viewers[stream_id] = set()
        
        self.viewers[stream_id].add(connection)
        self.connections[websocket] = connection
        
        logger.info(f"Viewer connected: user_id={user_id}, stream_id={stream_id}, total_viewers={len(self.viewers[stream_id])}")
        
        # Notify viewer that they're connected
        await websocket.send_json({
            "type": "connected",
            "role": "viewer",
            "stream_id": stream_id,
            "viewer_count": len(self.viewers[stream_id])
        })
        
        # Update broadcaster with new viewer count
        await self.send_to_broadcaster(stream_id, {
            "type": "viewer_count",
            "count": len(self.viewers[stream_id])
        })
        
        return {"success": True, "role": "viewer", "stream_id": stream_id}

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebRTC connection"""
        if websocket not in self.connections:
            return
        
        connection = self.connections[websocket]
        stream_id = connection.stream_id
        user_id = connection.user_id
        
        if connection.role == 'broadcaster':
            # Remove broadcaster
            if stream_id in self.broadcasters:
                del self.broadcasters[stream_id]
            
            # Remove from active streams
            if user_id in self.active_streams_by_user:
                del self.active_streams_by_user[user_id]
            
            # Notify all viewers that stream ended
            if stream_id in self.viewers:
                for viewer in list(self.viewers[stream_id]):
                    try:
                        if viewer.websocket in self.connections:
                            asyncio.create_task(viewer.websocket.send_json({
                                "type": "broadcaster_disconnected",
                                "message": "Stream has ended"
                            }))
                    except Exception as e:
                        logger.error(f"Error notifying viewer: {e}")
                
                # Clear viewers
                del self.viewers[stream_id]
            
            logger.info(f"Broadcaster disconnected: user_id={user_id}, stream_id={stream_id}")
        
        elif connection.role == 'viewer':
            # Remove viewer
            if stream_id in self.viewers:
                self.viewers[stream_id].discard(connection)
                
                if not self.viewers[stream_id]:
                    del self.viewers[stream_id]
                else:
                    # Update broadcaster with new viewer count
                    asyncio.create_task(self.send_to_broadcaster(stream_id, {
                        "type": "viewer_count",
                        "count": len(self.viewers[stream_id])
                    }))
            
            logger.info(f"Viewer disconnected: user_id={user_id}, stream_id={stream_id}")
        
        del self.connections[websocket]

    async def handle_signal(self, websocket: WebSocket, data: dict):
        """Handle WebRTC signaling messages"""
        if websocket not in self.connections:
            return
        
        connection = self.connections[websocket]
        stream_id = connection.stream_id
        signal_type = data.get("type")
        
        if connection.role == 'broadcaster':
            # Broadcaster -> Viewer signals (answer, ice_candidate)
            target_peer_id = data.get("target")
            
            if signal_type in ['answer', 'ice_candidate']:
                # Send to specific viewer
                await self.send_to_viewer(stream_id, target_peer_id, data)
        
        elif connection.role == 'viewer':
            # Viewer -> Broadcaster signals (offer, ice_candidate)
            if signal_type in ['offer', 'ice_candidate']:
                # Add viewer's peer_id for broadcaster to respond
                data['source'] = connection.peer_id
                await self.send_to_broadcaster(stream_id, data)

    async def send_to_broadcaster(self, stream_id: int, message: dict):
        """Send a message to the broadcaster of a stream"""
        if stream_id not in self.broadcasters:
            return
        
        broadcaster = self.broadcasters[stream_id]
        try:
            await broadcaster.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to broadcaster: {e}")
            self.disconnect(broadcaster.websocket)

    async def send_to_viewer(self, stream_id: int, peer_id: str, message: dict):
        """Send a message to a specific viewer"""
        if stream_id not in self.viewers:
            return
        
        for viewer in self.viewers[stream_id]:
            if viewer.peer_id == peer_id:
                try:
                    await viewer.websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to viewer: {e}")
                    self.disconnect(viewer.websocket)
                break

    async def broadcast_to_viewers(self, stream_id: int, message: dict):
        """Broadcast a message to all viewers of a stream"""
        if stream_id not in self.viewers:
            return
        
        disconnected = set()
        for viewer in self.viewers[stream_id]:
            try:
                await viewer.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to viewer: {e}")
                disconnected.add(viewer)
        
        # Clean up disconnected viewers
        for viewer in disconnected:
            self.disconnect(viewer.websocket)

    def get_viewer_count(self, stream_id: int) -> int:
        """Get the number of viewers for a stream"""
        return len(self.viewers.get(stream_id, set()))

    def is_user_streaming(self, user_id: int) -> Optional[int]:
        """Check if a user is currently streaming, returns stream_id if yes"""
        return self.active_streams_by_user.get(user_id)

    def get_active_streams(self) -> Dict[int, dict]:
        """Get all active streams with their details"""
        return {
            stream_id: {
                "stream_id": stream_id,
                "broadcaster_id": broadcaster.user_id,
                "viewer_count": self.get_viewer_count(stream_id),
                "started_at": broadcaster.connected_at.isoformat()
            }
            for stream_id, broadcaster in self.broadcasters.items()
        }

# Import asyncio for async tasks
import asyncio

# Global WebRTC manager instance
webrtc_manager = WebRTCManager()
