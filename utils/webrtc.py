import asyncio
import json
import uuid
import logging
from typing import Dict, List

logger = logging.getLogger("webrtc")

# Simplified data structures without aiortc dependencies
peer_connections = {}
broadcasters = {}

class SimplifiedWebRTCManager:
    """
    A simplified WebRTC manager that provides basic functionality
    without requiring aiortc dependencies
    """
    
    def __init__(self):
        self.connections = {}
        self.active_broadcasters = {}
        self.viewer_counts = {}
        self.signaling_connections = {}  # Store WebSocket connections for signaling

    async def create_connection(self, connection_id: str, connection_type: str = "peer"):
        """Create a simplified connection object"""
        connection = {
            "id": connection_id,
            "type": connection_type,
            "state": "new",
            "created_at": asyncio.get_event_loop().time()
        }
        self.connections[connection_id] = connection
        return connection

    async def close_connection(self, connection_id: str):
        """Close a connection"""
        if connection_id in self.connections:
            self.connections[connection_id]["state"] = "closed"
            logger.info(f"Connection {connection_id} closed")

    async def add_signaling_connection(self, stream_id: int, client_id: str, websocket):
        """Add a WebSocket connection for signaling"""
        if stream_id not in self.signaling_connections:
            self.signaling_connections[stream_id] = {}
        self.signaling_connections[stream_id][client_id] = websocket
        logger.info(f"Added signaling connection for stream {stream_id}, client {client_id}")

    async def remove_signaling_connection(self, stream_id: int, client_id: str):
        """Remove a WebSocket connection"""
        if stream_id in self.signaling_connections and client_id in self.signaling_connections[stream_id]:
            del self.signaling_connections[stream_id][client_id]
            if not self.signaling_connections[stream_id]:
                del self.signaling_connections[stream_id]
            logger.info(f"Removed signaling connection for stream {stream_id}, client {client_id}")

    async def forward_to_viewers(self, stream_id: int, broadcaster_id: str, message):
        """Forward a message from broadcaster to all viewers"""
        if stream_id in self.signaling_connections:
            for client_id, websocket in self.signaling_connections[stream_id].items():
                if client_id != broadcaster_id:  # Don't send back to broadcaster
                    try:
                        await websocket.send_text(json.dumps(message))
                        logger.info(f"Forwarded message to viewer {client_id}")
                    except Exception as e:
                        logger.error(f"Failed to forward to viewer {client_id}: {e}")

    async def forward_to_broadcaster(self, stream_id: int, viewer_id: str, message):
        """Forward a message from viewer to broadcaster"""
        if stream_id in broadcasters:
            for broadcaster_id in broadcasters.keys():
                if str(broadcasters[broadcaster_id]["stream_id"]) == str(stream_id):
                    if stream_id in self.signaling_connections and broadcaster_id in self.signaling_connections[stream_id]:
                        try:
                            await self.signaling_connections[stream_id][broadcaster_id].send_text(json.dumps(message))
                            logger.info(f"Forwarded message from viewer {viewer_id} to broadcaster {broadcaster_id}")
                        except Exception as e:
                            logger.error(f"Failed to forward to broadcaster {broadcaster_id}: {e}")

    async def forward_ice_candidate(self, stream_id: int, sender_id: str, message):
        """Forward ICE candidate to appropriate peer"""
        target_client = message.get("target_client")
        if target_client and stream_id in self.signaling_connections and target_client in self.signaling_connections[stream_id]:
            try:
                await self.signaling_connections[stream_id][target_client].send_text(json.dumps(message))
                logger.info(f"Forwarded ICE candidate from {sender_id} to {target_client}")
            except Exception as e:
                logger.error(f"Failed to forward ICE candidate: {e}")

    async def notify_broadcaster_viewer_ready(self, stream_id: int, viewer_id: str):
        """Notify broadcaster that a viewer is ready to receive stream"""
        if stream_id in broadcasters:
            for broadcaster_id in broadcasters.keys():
                if str(broadcasters[broadcaster_id]["stream_id"]) == str(stream_id):
                    if stream_id in self.signaling_connections and broadcaster_id in self.signaling_connections[stream_id]:
                        message = {
                            "type": "viewer-joined",
                            "viewer_id": viewer_id,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                        try:
                            await self.signaling_connections[stream_id][broadcaster_id].send_text(json.dumps(message))
                            logger.info(f"Notified broadcaster {broadcaster_id} about viewer {viewer_id}")
                        except Exception as e:
                            logger.error(f"Failed to notify broadcaster: {e}")

# Global manager instance
webrtc_manager = SimplifiedWebRTCManager()

async def create_broadcaster(broadcaster_id, stream_id):
    """Create a new broadcaster for a given stream - simplified version"""
    logger.info(f"Creating broadcaster {broadcaster_id} for stream {stream_id}")
    
    # Clean up existing broadcaster if exists
    if broadcaster_id in broadcasters:
        await cleanup_broadcaster(broadcaster_id)
    
    # Create simplified broadcaster data
    broadcaster_data = {
        "id": broadcaster_id,
        "stream_id": stream_id,
        "tracks": {},
        "viewers": set(),
        "state": "active",
        "created_at": asyncio.get_event_loop().time()
    }
    
    broadcasters[broadcaster_id] = broadcaster_data
    
    # Create a simplified connection
    connection = await webrtc_manager.create_connection(broadcaster_id, "broadcaster")
    
    logger.info(f"Broadcaster {broadcaster_id} created successfully")
    return connection

async def create_viewer(viewer_id, broadcaster_id):
    """Create a new viewer connection to watch a broadcaster - simplified version"""
    logger.info(f"Creating viewer {viewer_id} for broadcaster {broadcaster_id}")
    
    if broadcaster_id not in broadcasters:
        logger.warning(f"Broadcaster {broadcaster_id} not found")
        return None
    
    # Clean up existing viewer connection if exists
    if viewer_id in peer_connections:
        await webrtc_manager.close_connection(viewer_id)
    
    # Create simplified viewer connection
    connection = await webrtc_manager.create_connection(viewer_id, "viewer")
    peer_connections[viewer_id] = connection
    
    # Add viewer to broadcaster's viewer list
    broadcasters[broadcaster_id]["viewers"].add(viewer_id)
    
    logger.info(f"Viewer {viewer_id} connected to broadcaster {broadcaster_id}")
    return connection

async def cleanup_broadcaster(broadcaster_id):
    """Clean up a broadcaster and all its viewers"""
    if broadcaster_id not in broadcasters:
        return
    
    broadcaster_data = broadcasters[broadcaster_id]
    
    # Close all viewer connections
    for viewer_id in broadcaster_data["viewers"].copy():
        if viewer_id in peer_connections:
            await webrtc_manager.close_connection(viewer_id)
            del peer_connections[viewer_id]
    
    # Remove broadcaster
    del broadcasters[broadcaster_id]
    logger.info(f"Broadcaster {broadcaster_id} cleaned up")

def get_viewer_count(broadcaster_id):
    """Get number of viewers for a broadcaster"""
    if broadcaster_id in broadcasters:
        return len(broadcasters[broadcaster_id]["viewers"])
    return 0

def get_active_broadcasters():
    """Get list of active broadcasters"""
    return list(broadcasters.keys())

def get_broadcaster_info(broadcaster_id):
    """Get detailed info about a broadcaster"""
    if broadcaster_id in broadcasters:
        broadcaster_data = broadcasters[broadcaster_id].copy()
        broadcaster_data["viewers"] = list(broadcaster_data["viewers"])  # Convert set to list
        return broadcaster_data
    return None

def get_all_connections():
    """Get information about all active connections"""
    return {
        "broadcasters": len(broadcasters),
        "viewers": len(peer_connections),
        "total_connections": len(broadcasters) + len(peer_connections),
        "active_broadcasters": list(broadcasters.keys())
    }

async def handle_offer(client_id: str, sdp: str, stream_id: str, is_broadcaster: bool = False):
    """Handle WebRTC offer - simplified version"""
    logger.info(f"Handling offer from {client_id}, stream: {stream_id}, broadcaster: {is_broadcaster}")
    
    if is_broadcaster:
        connection = await create_broadcaster(client_id, stream_id)
    else:
        # For viewers, find the broadcaster for this stream
        broadcaster_id = None
        for bid, bdata in broadcasters.items():
            # Compare as strings since stream_id comes as string from API
            if str(bdata["stream_id"]) == str(stream_id):
                broadcaster_id = bid
                break
        
        if broadcaster_id:
            connection = await create_viewer(client_id, broadcaster_id)
        else:
            logger.warning(f"No broadcaster found for stream {stream_id}")
            logger.info(f"Available broadcasters: {list(broadcasters.keys())}")
            logger.info(f"Broadcaster stream IDs: {[bdata['stream_id'] for bdata in broadcasters.values()]}")
            return None
    
    if not connection:
        logger.error(f"Failed to create connection for {client_id}")
        return None
    
    # Return successful connection result
    return {
        "connection": connection,
        "client_id": client_id,
        "stream_id": stream_id,
        "is_broadcaster": is_broadcaster
    }

async def handle_ice_candidate(client_id: str, candidate: dict):
    """Handle ICE candidate - simplified version"""
    logger.info(f"Handling ICE candidate from {client_id}")
    
    # In a real implementation, this would handle ICE candidates
    # For now, we just log and acknowledge
    return {"status": "received", "client_id": client_id}

# Compatibility functions for existing code
async def cleanup_all_connections():
    """Clean up all connections"""
    for broadcaster_id in list(broadcasters.keys()):
        await cleanup_broadcaster(broadcaster_id)
    
    for viewer_id in list(peer_connections.keys()):
        await webrtc_manager.close_connection(viewer_id)
    
    peer_connections.clear()
    logger.info("All connections cleaned up")
