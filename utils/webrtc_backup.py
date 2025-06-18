import asyncio
import json
import uuid
import logging
from typing import Dict, List

logger = logging.getLogger("webrtc")

# Simplified implementations that don't require aiortc
peer_connections = {}
broadcasters = {}

class StreamTrack:
    """
    A simplified video stream track placeholder
    """
    def __init__(self, track=None, broadcaster_id=None):
        self.track = track
        self.broadcaster_id = broadcaster_id
        self.kind = "video"

    async def recv(self):
        # Placeholder implementation
        return None

async def create_broadcaster(client_id: str, stream_id: str):
    """Create a broadcaster peer connection - simplified version"""
    logger.info(f"Creating broadcaster for client {client_id}, stream {stream_id}")
    
    # Store broadcaster info
    broadcasters[client_id] = {
        "stream_id": stream_id,
        "created_at": asyncio.get_event_loop().time()
    }
    
    return {
        "client_id": client_id,
        "stream_id": stream_id,
        "status": "created"
    }

async def create_viewer(client_id: str, stream_id: str):
    """Create a viewer peer connection - simplified version"""
    logger.info(f"Creating viewer for client {client_id}, stream {stream_id}")
    
    # Store viewer info
    peer_connections[client_id] = {
        "stream_id": stream_id,
        "type": "viewer",
        "created_at": asyncio.get_event_loop().time()
    }
    
    return {
        "client_id": client_id,
        "stream_id": stream_id,
        "status": "created"
    }

def get_viewer_count(stream_id: str) -> int:
    """Get the number of viewers for a stream"""
    count = 0
    for client_id, info in peer_connections.items():
        if info.get("stream_id") == stream_id and info.get("type") == "viewer":
            count += 1
    return count

def get_active_broadcasters() -> List[str]:
    """Get list of active broadcaster IDs"""
    return list(broadcasters.keys())

async def cleanup_peer_connection(client_id: str):
    """Clean up a peer connection"""
    if client_id in peer_connections:
        del peer_connections[client_id]
        logger.info(f"Cleaned up peer connection for client {client_id}")
    
    if client_id in broadcasters:
        del broadcasters[client_id]
        logger.info(f"Cleaned up broadcaster for client {client_id}")

def get_connection_stats():
    """Get connection statistics"""
    return {
        "total_connections": len(peer_connections),
        "active_broadcasters": len(broadcasters),
        "viewers": len([c for c in peer_connections.values() if c.get("type") == "viewer"])
    }
