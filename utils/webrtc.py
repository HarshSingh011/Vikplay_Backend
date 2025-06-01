import asyncio
import json
import uuid
import logging
from typing import Dict, List
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCIceCandidate
from aiortc.contrib.media import MediaRelay

logger = logging.getLogger("webrtc")

# Media relay for broadcasting streams to multiple viewers
relay = MediaRelay()

# Store active peer connections
peer_connections = {}

# Store active broadcasters
broadcasters = {}

class StreamTrack(MediaStreamTrack):
    """
    A video stream track that forwards frames from a broadcaster to viewers
    """
    kind = "video"

    def __init__(self, track, broadcaster_id):
        super().__init__()
        self.track = track
        self.broadcaster_id = broadcaster_id

    async def recv(self):
        frame = await self.track.recv()
        return frame

async def create_broadcaster(broadcaster_id, stream_id):
    """Create a new broadcaster for a given stream"""
    if broadcaster_id in broadcasters:
        pc = broadcasters[broadcaster_id]["pc"]
        await pc.close()
        
    pc = RTCPeerConnection()
    broadcasters[broadcaster_id] = {
        "pc": pc,
        "stream_id": stream_id,
        "tracks": {},
        "viewers": set()
    }
    
    @pc.on("track")
    def on_track(track):
        logger.info(f"Broadcaster {broadcaster_id} added track: {track.kind}")
        if track.kind == "video":
            broadcasters[broadcaster_id]["tracks"]["video"] = relay.subscribe(track)
        elif track.kind == "audio":
            broadcasters[broadcaster_id]["tracks"]["audio"] = relay.subscribe(track)
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Broadcaster {broadcaster_id} connection state: {pc.connectionState}")
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            if broadcaster_id in broadcasters:
                # Notify viewers the stream has ended
                for viewer_id in broadcasters[broadcaster_id]["viewers"]:
                    if viewer_id in peer_connections:
                        await peer_connections[viewer_id].close()
                        del peer_connections[viewer_id]
                
                del broadcasters[broadcaster_id]
    
    return pc

async def create_viewer(viewer_id, broadcaster_id):
    """Create a new viewer connection to watch a broadcaster"""
    if broadcaster_id not in broadcasters:
        return None
    
    if viewer_id in peer_connections:
        pc = peer_connections[viewer_id]
        await pc.close()
    
    pc = RTCPeerConnection()
    peer_connections[viewer_id] = pc
    
    # Add broadcaster's tracks to viewer
    broadcaster_data = broadcasters[broadcaster_id]
    
    if "video" in broadcaster_data["tracks"]:
        video_track = broadcaster_data["tracks"]["video"]
        pc.addTrack(StreamTrack(video_track, broadcaster_id))
    
    if "audio" in broadcaster_data["tracks"]:
        audio_track = broadcaster_data["tracks"]["audio"]
        pc.addTrack(audio_track)
    
    # Add viewer to broadcaster's viewer list
    broadcaster_data["viewers"].add(viewer_id)
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Viewer {viewer_id} connection state: {pc.connectionState}")
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            if viewer_id in peer_connections:
                del peer_connections[viewer_id]
                
                # Remove viewer from broadcaster's viewer list
                if broadcaster_id in broadcasters:
                    broadcasters[broadcaster_id]["viewers"].discard(viewer_id)
    
    return pc

def get_viewer_count(broadcaster_id):
    """Get number of viewers for a broadcaster"""
    if broadcaster_id in broadcasters:
        return len(broadcasters[broadcaster_id]["viewers"])
    return 0

def get_active_broadcasters():
    """Get list of active broadcasters"""
    return list(broadcasters.keys())