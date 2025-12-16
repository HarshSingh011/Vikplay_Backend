from pydantic import BaseModel
from typing import Optional, Any

class WebRTCSignal(BaseModel):
    """WebRTC signaling message"""
    type: str  # 'offer', 'answer', 'ice_candidate'
    data: Optional[Any] = None
    target: Optional[str] = None  # peer_id for targeted messages
    source: Optional[str] = None  # peer_id of sender

class WebRTCOffer(BaseModel):
    """WebRTC offer from viewer"""
    sdp: str
    type: str = "offer"

class WebRTCAnswer(BaseModel):
    """WebRTC answer from broadcaster"""
    sdp: str
    type: str = "answer"
    target: str  # viewer peer_id

class WebRTCIceCandidate(BaseModel):
    """ICE candidate for WebRTC connection"""
    candidate: str
    sdpMLineIndex: int
    sdpMid: str
    target: Optional[str] = None  # for broadcaster -> viewer

class StreamSessionInfo(BaseModel):
    """Information about active stream session"""
    stream_id: int
    user_id: int
    role: str
    viewer_count: Optional[int] = 0
