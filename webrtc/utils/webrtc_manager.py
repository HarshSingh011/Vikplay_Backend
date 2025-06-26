import asyncio
import json
import uuid
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("webrtc")

class WebRTCManager:
    """
    Enhanced WebRTC manager for handling streams, connections, and signaling
    """
    
    def __init__(self):
        self.connections = {}
        self.active_broadcasters = {}
        self.viewer_counts = {}
        self.websocket_connections = {}  # Store WebSocket connections by stream_id -> client_id -> websocket
        self.streams = {}  # Store stream information

    def add_websocket_connection(self, stream_id: str, client_id: str, websocket):
        """Add a WebSocket connection for a client in a stream"""
        if stream_id not in self.websocket_connections:
            self.websocket_connections[stream_id] = {}
        self.websocket_connections[stream_id][client_id] = websocket
        logger.info(f"Added WebSocket connection for stream {stream_id}, client {client_id}")

    def remove_websocket_connection(self, stream_id: str, client_id: str):
        """Remove a WebSocket connection"""
        if stream_id in self.websocket_connections and client_id in self.websocket_connections[stream_id]:
            del self.websocket_connections[stream_id][client_id]
            if not self.websocket_connections[stream_id]:  # Clean up empty stream
                del self.websocket_connections[stream_id]
            logger.info(f"Removed WebSocket connection for stream {stream_id}, client {client_id}")

    async def broadcast_to_stream(self, stream_id: str, message: str, exclude_client: Optional[str] = None):
        """Broadcast a message to all clients in a stream"""
        if stream_id not in self.websocket_connections:
            return
        
        for client_id, websocket in self.websocket_connections[stream_id].items():
            if exclude_client and client_id == exclude_client:
                continue
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")

    async def handle_signaling_message(self, stream_id: str, client_id: str, message: dict):
        """Handle signaling messages between clients"""
        message_type = message.get("type")
        
        if message_type == "offer":
            # Forward offer to other clients (for peer-to-peer connections)
            await self.broadcast_to_stream(stream_id, json.dumps(message), exclude_client=client_id)
        elif message_type == "answer":
            # Forward answer to the appropriate client
            target_client = message.get("target_client")
            if target_client and stream_id in self.websocket_connections:
                if target_client in self.websocket_connections[stream_id]:
                    try:
                        await self.websocket_connections[stream_id][target_client].send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Failed to forward answer to {target_client}: {e}")
        elif message_type == "ice-candidate":
            # Forward ICE candidate to all other clients
            await self.broadcast_to_stream(stream_id, json.dumps(message), exclude_client=client_id)
        elif message_type == "chat":
            # Broadcast chat message to all clients
            await self.broadcast_to_stream(stream_id, json.dumps(message))

    def handle_answer(self, stream_id: str, client_id: str, sdp: str):
        """Handle WebRTC answer"""
        logger.info(f"Handling answer from client {client_id} for stream {stream_id}")
        # In a real implementation, this would process the SDP answer
        return {"success": True, "message": "Answer processed"}

    def cleanup_stream(self, stream_id: str):
        """Clean up all connections for a stream"""
        if stream_id in self.websocket_connections:
            for client_id in list(self.websocket_connections[stream_id].keys()):
                self.remove_websocket_connection(stream_id, client_id)
        
        # Clean up other stream-related data
        if stream_id in self.active_broadcasters:
            del self.active_broadcasters[stream_id]
        if stream_id in self.viewer_counts:
            del self.viewer_counts[stream_id]
        
        logger.info(f"Cleaned up stream {stream_id}")

# Global manager instance
webrtc_manager = WebRTCManager()

def create_broadcaster(stream_id: str, client_id: str, sdp: str):
    """Create a new broadcaster for a stream"""
    logger.info(f"Creating broadcaster {client_id} for stream {stream_id}")
    
    # Store broadcaster information
    webrtc_manager.active_broadcasters[stream_id] = {
        "client_id": client_id,
        "sdp": sdp,
        "created_at": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    }
    
    return {
        "success": True,
        "stream_id": stream_id,
        "client_id": client_id,
        "answer": generate_mock_answer(sdp)  # In real implementation, this would be proper SDP
    }

def create_viewer(stream_id: str, client_id: str, sdp: str):
    """Create a new viewer for a stream"""
    logger.info(f"Creating viewer {client_id} for stream {stream_id}")
    
    # Check if broadcaster exists
    if stream_id not in webrtc_manager.active_broadcasters:
        return {
            "success": False,
            "error": f"No broadcaster found for stream {stream_id}"
        }
    
    # Update viewer count
    if stream_id not in webrtc_manager.viewer_counts:
        webrtc_manager.viewer_counts[stream_id] = 0
    webrtc_manager.viewer_counts[stream_id] += 1
    
    return {
        "success": True,
        "stream_id": stream_id,
        "client_id": client_id,
        "answer": generate_mock_answer(sdp)  # In real implementation, this would be proper SDP
    }

def handle_offer(stream_id: str, client_id: str, sdp: str, is_broadcaster: bool = False):
    """Handle WebRTC offer"""
    if is_broadcaster:
        return create_broadcaster(stream_id, client_id, sdp)
    else:
        return create_viewer(stream_id, client_id, sdp)

def handle_ice_candidate(stream_id: str, client_id: str, candidate: dict):
    """Handle ICE candidate"""
    logger.info(f"Handling ICE candidate from {client_id} for stream {stream_id}")
    
    # In a real implementation, this would process the ICE candidate
    return {
        "success": True,
        "stream_id": stream_id,
        "client_id": client_id,
        "message": "ICE candidate processed"
    }

def get_viewer_count(stream_id: str) -> int:
    """Get the number of viewers for a stream"""
    return webrtc_manager.viewer_counts.get(stream_id, 0)

def generate_mock_answer(offer_sdp: str) -> str:
    """Generate a mock SDP answer (for testing purposes)"""
    # This is a simplified mock answer
    # In a real implementation, you would use a proper WebRTC library
    return f"""v=0
o=- {uuid.uuid4().hex[:10]} 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0
a=msid-semantic: WMS
m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:mock
a=ice-pwd:mockpassword
a=ice-options:trickle
a=fingerprint:sha-256 Mock:Fingerprint:For:Testing
a=setup:active
a=mid:0
a=sendonly
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:96 VP8/90000
a=ssrc:{uuid.uuid4().hex[:8]} cname:mock-cname
"""
