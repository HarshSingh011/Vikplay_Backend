"""
Video Module - Clean Architecture Implementation
Contains video management functionality with automatic data collection for AI
"""

from .routes import router as video_router

# For backward compatibility
router = video_router

__all__ = [
    "video_router",
    "router"
]
