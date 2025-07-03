"""
Video Module - Contains video management functionality with automatic data collection for AI
"""

from .routes.video_routes_clean import router as video_router

# For backward compatibility
router = video_router

__all__ = [
    "video_router",
    "router"
]

# Alias for convenience
router = video_router
