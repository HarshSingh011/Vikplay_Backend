"""
Video Module Main Router
Combines all video-related routes following clean architecture principles
"""
from fastapi import APIRouter

from .video_crud import router as crud_router
from .video_tracking import router as tracking_router
from .video_search import router as search_router
from .video_session import router as session_router
from .video_analytics import router as analytics_router
from .video_categories import router as categories_router

# Main router with common prefix
router = APIRouter(prefix="/api/videos", tags=["video-module"])

# Include all sub-routers
router.include_router(crud_router, prefix="", tags=["video-crud"])
router.include_router(tracking_router, prefix="", tags=["video-tracking"])
router.include_router(search_router, prefix="", tags=["video-search"])
router.include_router(session_router, prefix="", tags=["video-session"])
router.include_router(analytics_router, prefix="", tags=["video-analytics"])
router.include_router(categories_router, prefix="", tags=["video-categories"])
