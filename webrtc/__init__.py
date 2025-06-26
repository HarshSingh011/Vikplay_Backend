"""
WebRTC module - handles real-time communication and signaling
"""
from .routes import router
from .utils import webrtc_manager

__all__ = [
    # Routes
    "router",
    # Utils
    "webrtc_manager"
]
