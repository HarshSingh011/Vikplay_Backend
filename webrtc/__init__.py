"""
WebRTC module - handles real-time communication and signaling
"""
from .routes.webrtc import router as webrtc_router

__all__ = [
    "webrtc_router", 
    "router"
]

# Alias for convenience
router = webrtc_router
