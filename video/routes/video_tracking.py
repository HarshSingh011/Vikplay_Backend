"""
Video Tracking Routes - AI Data Collection
Handles automatic data collection for AI recommendations
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import AnalyticsService
from video.repositories.video_repository import (
    VideoRepository, UserVideoHistoryRepository, UserSearchHistoryRepository,
    UserSessionRepository, VideoInteractionRepository
)
from video.schemas.video_schemas import (
    WatchProgressUpdateEnhanced, VideoEngagement, VideoInteraction,
    WatchProgressWithAuth, EngagementWithAuth, InteractionWithAuth
)
from video.utils import extract_device_info

router = APIRouter(prefix="/track")

# ====== DEPENDENCY INJECTION ======

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency injection for AnalyticsService"""
    video_repo = VideoRepository(db)
    history_repo = UserVideoHistoryRepository(db)
    search_repo = UserSearchHistoryRepository(db)
    session_repo = UserSessionRepository(db)
    interaction_repo = VideoInteractionRepository(db)
    return AnalyticsService(video_repo, history_repo, search_repo, session_repo, interaction_repo)

# ====== TRACKING ENDPOINTS ======

@router.post("/watch-progress")
async def track_watch_progress(
    progress_data: WatchProgressWithAuth,
    request: Request,
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    AUTOMATIC COLLECTION: Viewing History
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(progress_data, db)
    
    # Extract device info
    device_info = extract_device_info(request)
    
    # Update progress data with device info
    progress_update = WatchProgressUpdateEnhanced(
        **progress_data.model_dump(exclude={'access_token'}),
        device_type=device_info["device_type"]
    )
    
    return await analytics_service.track_viewing_progress(current_user["user_id"], progress_update)


@router.post("/engagement")
async def track_engagement(
    engagement_data: EngagementWithAuth,
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    AUTOMATIC COLLECTION: Engagement Metrics
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(engagement_data, db)
    
    # Remove access_token from engagement data
    engagement_update = VideoEngagement(**engagement_data.model_dump(exclude={'access_token'}))
    
    return await analytics_service.track_engagement(current_user["user_id"], engagement_update)


@router.post("/interaction")
async def track_interaction(
    interaction_data: InteractionWithAuth,
    request: Request,
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    AUTOMATIC COLLECTION: Detailed Engagement
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(interaction_data, db)
    
    # Extract device info
    device_info = extract_device_info(request)
    
    # Update interaction data with device info
    interaction_update = VideoInteraction(
        **interaction_data.model_dump(exclude={'access_token'}),
        device_type=device_info["device_type"]
    )
    
    return await analytics_service.track_interaction(current_user["user_id"], interaction_update)
