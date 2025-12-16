"""
Video Routes - Clean Architecture with Access Token Support
Enhanced FastAPI routes following clean architecture principles
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import VideoService, AnalyticsService, SearchService, SessionService
from video.repositories.video_repository import (
    VideoRepository, CategoryRepository, UserVideoHistoryRepository,
    UserSearchHistoryRepository, UserSessionRepository, VideoInteractionRepository
)
from video.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse, CategoryCreate, CategoryResponse,
    WatchProgressUpdateEnhanced, VideoEngagement, VideoInteraction,
    SearchQueryLog, SearchResultClick, SessionStart, SessionActivity, SessionEnd,
    UserVideoHistoryResponse, UserSearchHistoryResponse, UserSessionResponse,
    UserPreferencesUpdate, UserAnalytics, VideoAnalytics
)

router = APIRouter(prefix="/api/videos", tags=["videos"])


# ====== AUTHENTICATION SCHEMAS ======

class AuthenticatedRequest(BaseModel):
    """Base schema for requests with access token in body"""
    access_token: str


class VideoCreateWithAuth(VideoCreate, AuthenticatedRequest):
    """Video creation with authentication"""
    pass


class VideoUpdateWithAuth(VideoUpdate, AuthenticatedRequest):
    """Video update with authentication"""
    pass


class VideoDeleteWithAuth(AuthenticatedRequest):
    """Video deletion with authentication (only token needed)"""
    pass


class CategoryCreateWithAuth(CategoryCreate, AuthenticatedRequest):
    """Category creation with authentication"""
    pass


class AnalyticsRequest(AuthenticatedRequest):
    """Analytics request with authentication"""
    pass


class UserHistoryRequest(AuthenticatedRequest):
    """User history request with authentication"""
    skip: int = 0
    limit: int = 50


class WatchProgressWithAuth(WatchProgressUpdateEnhanced, AuthenticatedRequest):
    """Watch progress tracking with authentication"""
    pass


class EngagementWithAuth(VideoEngagement, AuthenticatedRequest):
    """Engagement tracking with authentication"""
    pass


class InteractionWithAuth(VideoInteraction, AuthenticatedRequest):
    """Interaction tracking with authentication"""
    pass


class SearchWithAuth(SearchQueryLog, AuthenticatedRequest):
    """Search with authentication"""
    pass


class SearchClickWithAuth(SearchResultClick, AuthenticatedRequest):
    """Search click tracking with authentication"""
    pass


class SessionStartWithAuth(SessionStart, AuthenticatedRequest):
    """Session start with authentication"""
    pass


class SessionActivityWithAuth(SessionActivity, AuthenticatedRequest):
    """Session activity with authentication"""
    pass


class SessionEndWithAuth(SessionEnd, AuthenticatedRequest):
    """Session end with authentication"""
    pass


# ====== DEPENDENCY INJECTION ======

def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    """Dependency injection for VideoService"""
    video_repo = VideoRepository(db)
    category_repo = CategoryRepository(db)
    return VideoService(video_repo, category_repo)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency injection for AnalyticsService"""
    video_repo = VideoRepository(db)
    history_repo = UserVideoHistoryRepository(db)
    search_repo = UserSearchHistoryRepository(db)
    session_repo = UserSessionRepository(db)
    interaction_repo = VideoInteractionRepository(db)
    return AnalyticsService(video_repo, history_repo, search_repo, session_repo, interaction_repo)


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """Dependency injection for SearchService"""
    video_repo = VideoRepository(db)
    search_repo = UserSearchHistoryRepository(db)
    return SearchService(video_repo, search_repo)


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """Dependency injection for SessionService"""
    session_repo = UserSessionRepository(db)
    return SessionService(session_repo)


def extract_device_info(request: Request) -> Dict[str, Any]:
    """Extract device information from request"""
    user_agent = request.headers.get("user-agent", "")
    
    device_type = "desktop"
    if "mobile" in user_agent.lower():
        device_type = "mobile"
    elif "tablet" in user_agent.lower():
        device_type = "tablet"
    
    browser = "unknown"
    if "chrome" in user_agent.lower():
        browser = "chrome"
    elif "firefox" in user_agent.lower():
        browser = "firefox"
    elif "safari" in user_agent.lower():
        browser = "safari"
    elif "edge" in user_agent.lower():
        browser = "edge"
    
    os = "unknown"
    if "windows" in user_agent.lower():
        os = "windows"
    elif "mac" in user_agent.lower():
        os = "macos"
    elif "linux" in user_agent.lower():
        os = "linux"
    elif "android" in user_agent.lower():
        os = "android"
    elif "ios" in user_agent.lower():
        os = "ios"
    
    return {
        "device_type": device_type,
        "browser": browser,
        "os": os,
        "ip_address": request.client.host if request.client else None,
        "user_agent": user_agent
    }


# ====== BASIC CRUD OPERATIONS ======

@router.post("/", response_model=VideoResponse)
async def create_video(
    video_data: VideoCreateWithAuth,
    db: Session = Depends(get_db),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Create a new video
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(video_data, db)
    
    # Remove access_token from video data
    video_create_data = VideoCreate(**video_data.model_dump(exclude={'access_token'}))
    
    return await video_service.create_video(video_create_data)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    video_service: VideoService = Depends(get_video_service)
):
    """Get video by ID (public endpoint)"""
    return await video_service.get_video(video_id)


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    update_data: VideoUpdateWithAuth,
    db: Session = Depends(get_db),
    video_service: VideoService = Depends(get_video_service)
):
    """Update video by ID"""
    # Verify access token from request body
    current_user = verify_token_from_body(update_data, db)
    
    # Remove access token from update data
    video_update = VideoUpdate(**update_data.dict(exclude={'access_token'}))
    
    return await video_service.update_video(video_id, video_update)


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    delete_data: VideoDeleteWithAuth,
    db: Session = Depends(get_db),
    video_service: VideoService = Depends(get_video_service)
):
    """Delete video by ID"""
    # Verify access token from request body
    current_user = verify_token_from_body(delete_data, db)
    
    success = await video_service.delete_video(video_id)
    return {"status": "success", "message": "Video deleted successfully"}


@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    skip: int = 0,
    limit: int = 20,
    video_service: VideoService = Depends(get_video_service)
):
    """List videos with pagination"""
    videos = await video_service.get_videos(skip=skip, limit=limit)
    return videos


@router.get("/popular/", response_model=List[VideoResponse])
async def get_popular_videos(
    limit: int = 20,
    video_service: VideoService = Depends(get_video_service)
):
    """Get popular videos"""
    return await video_service.get_popular_videos(limit)


@router.get("/trending/", response_model=List[VideoResponse])
async def get_trending_videos(
    days: int = 7,
    limit: int = 20,
    video_service: VideoService = Depends(get_video_service)
):
    """Get trending videos"""
    return await video_service.get_trending_videos(days, limit)


# ====== AUTOMATIC DATA COLLECTION ENDPOINTS ======

@router.post("/track/watch-progress")
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


@router.post("/track/engagement")
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


@router.post("/track/interaction")
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


@router.post("/search")
async def search_videos_with_tracking(
    search_data: SearchWithAuth,
    request: Request,
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    """
    AUTOMATIC COLLECTION: Search Queries
    Enhanced search with automatic tracking
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(search_data, db)
    
    # Extract device info
    device_info = extract_device_info(request)
    
    # Update search data with device info
    search_query = SearchQueryLog(
        **search_data.model_dump(exclude={'access_token'}),
        device_type=device_info["device_type"]
    )
    
    return await search_service.search_with_tracking(current_user["user_id"], search_query)


@router.post("/search/click")
async def track_search_click(
    click_data: SearchClickWithAuth,
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    """
    AUTOMATIC COLLECTION: Search Result Clicks
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(click_data, db)
    
    # Remove access_token from click data
    click_update = click_data.model_dump(exclude={'access_token'})
    
    return await search_service.track_search_click(
        user_id=current_user["user_id"],
        search_id=click_update["search_id"],
        clicked_video_id=click_update["clicked_video_id"],
        click_position=click_update["click_position"],
        time_to_click=click_update.get("time_to_click")
    )


@router.post("/session/start")
async def start_session(
    session_data: SessionStartWithAuth,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """
    AUTOMATIC COLLECTION: Session Patterns
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(session_data, db)
    
    # Extract device info
    device_info = extract_device_info(request)
    
    return await session_service.start_session(
        user_id=current_user["user_id"],
        session_id=session_data.session_id,
        device_info=device_info
    )


@router.put("/session/activity")
async def update_session_activity(
    activity_data: SessionActivityWithAuth,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """
    AUTOMATIC COLLECTION: Session Activity
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(activity_data, db)
    
    # Remove access_token from activity data
    activity_update = activity_data.model_dump(exclude={'access_token'})
    
    return await session_service.update_session_activity(
        user_id=current_user["user_id"],
        session_id=activity_update["session_id"],
        activity_data=activity_update
    )


@router.post("/session/end")
async def end_session(
    session_data: SessionEndWithAuth,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """
    AUTOMATIC COLLECTION: Session End
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(session_data, db)
    
    return await session_service.end_session(
        user_id=current_user["user_id"],
        session_id=session_data.session_id,
        session_duration=session_data.session_duration
    )


# ====== ANALYTICS ENDPOINTS ======

@router.post("/analytics/user", response_model=UserAnalytics)
async def get_user_analytics(
    analytics_request: AnalyticsRequest,
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive user analytics for AI recommendations"""
    # Verify access token from request body
    current_user = verify_token_from_body(analytics_request, db)
    
    return await analytics_service.get_user_analytics(current_user["user_id"])


@router.post("/history/", response_model=List[UserVideoHistoryResponse])
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


# ====== CATEGORY MANAGEMENT ======

@router.post("/categories/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreateWithAuth,
    db: Session = Depends(get_db)
):
    """Create a new category"""
    # Verify access token from request body
    current_user = verify_token_from_body(category_data, db)
    
    category_repo = CategoryRepository(db)
    
    # Remove access token from category data
    category_create = CategoryCreate(**category_data.dict(exclude={'access_token'}))
    
    # Check if category already exists
    existing = category_repo.get_by_name(category_create.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists"
        )
    
    category = category_repo.create(category_create.model_dump())
    return CategoryResponse.model_validate(category)


@router.get("/categories/", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
):
    """List all categories with video counts"""
    category_repo = CategoryRepository(db)
    categories = category_repo.get_categories_with_video_count()
    
    return [
        CategoryResponse(
            id=cat["id"],
            name=cat["name"],
            description=cat["description"],
            created_at=cat["created_at"],
            video_count=cat["video_count"]
        )
        for cat in categories
    ]


@router.get("/categories/{category_id}/videos", response_model=List[VideoResponse])
async def get_videos_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 20,
    video_service: VideoService = Depends(get_video_service)
):
    """Get videos by category"""
    return await video_service.get_videos_by_category(category_id, skip, limit)
