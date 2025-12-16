"""
Video Module Main Router - Unified API Structure
Single clean video API without confusing duplicate groups
"""
from fastapi import APIRouter

from .video_crud import router as crud_router
from .video_tracking import router as tracking_router
from .video_search import router as search_router
from .video_session import router as session_router
from .video_analytics import router as analytics_router
from .video_categories import router as categories_router

# Main router with single unified tag
router = APIRouter(prefix="/api/videos", tags=["Videos"])

# Include all sub-routers with NO additional tags (unified under "Videos")
router.include_router(crud_router, prefix="")
router.include_router(tracking_router, prefix="")
router.include_router(search_router, prefix="")
router.include_router(session_router, prefix="")
router.include_router(analytics_router, prefix="")
router.include_router(categories_router, prefix="")
