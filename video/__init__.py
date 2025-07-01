"""
Video Module - Contains video management functionality
"""

from .routes.video_routes import router as video_router

__all__ = [
    "video_router",
    "router"
]

# Alias for convenience
router = video_router
