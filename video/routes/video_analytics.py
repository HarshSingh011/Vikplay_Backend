"""
Video Analytics Routes - Analytics and user data
Handles analytics endpoints and user history
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import AnalyticsService
from video.repositories.video_repository import (
    VideoRepository, UserVideoHistoryRepository, UserSearchHistoryRepository,
    UserSessionRepository, VideoInteractionRepository
)
from video.schemas.video_schemas import (
    UserAnalytics, UserVideoHistoryResponse, AnalyticsRequest, UserHistoryRequest
)

router = APIRouter(prefix="/analytics")

# ====== DEPENDENCY INJECTION ======

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency injection for AnalyticsService"""
    video_repo = VideoRepository(db)
    history_repo = UserVideoHistoryRepository(db)
    search_repo = UserSearchHistoryRepository(db)
    session_repo = UserSessionRepository(db)
    interaction_repo = VideoInteractionRepository(db)
    return AnalyticsService(video_repo, history_repo, search_repo, session_repo, interaction_repo)

# ====== ANALYTICS ENDPOINTS ======

@router.post("/user", response_model=UserAnalytics)
async def get_user_analytics(
    analytics_request: AnalyticsRequest,
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive user analytics for AI recommendations"""
    # Verify access token from request body
    current_user = verify_token_from_body(analytics_request, db)
    
    return await analytics_service.get_user_analytics(current_user["user_id"])


@router.post("/history", response_model=List[UserVideoHistoryResponse])
async def get_user_history(
    history_request: UserHistoryRequest,
    db: Session = Depends(get_db)
):
    """Get user's viewing history"""
    # Verify access token from request body
    current_user = verify_token_from_body(history_request, db)
    
    history_repo = UserVideoHistoryRepository(db)
    history = history_repo.get_user_history(
        current_user["user_id"], 
        history_request.skip, 
        history_request.limit
    )
    
    return [
        UserVideoHistoryResponse(
            id=h.id,
            user_id=h.user_id,
            video_id=h.video_id,
            watched_at=h.watched_at,
            watch_duration=h.watch_duration,
            completed=h.completion_percentage >= 90,
            last_position=h.watch_duration,
            rating=h.rating
        )
        for h in history
    ]
