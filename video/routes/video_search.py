"""
Video Search Routes - Search functionality with tracking
Handles video search operations and search behavior tracking
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import SearchService
from video.repositories.video_repository import (
    VideoRepository, UserSearchHistoryRepository
)
from video.schemas.video_schemas import (
    SearchQueryLog, SearchResultClick, SearchWithAuth, SearchClickWithAuth
)
from video.utils import extract_device_info

router = APIRouter(prefix="/search", tags=["search"])

# ====== DEPENDENCY INJECTION ======

def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """Dependency injection for SearchService"""
    video_repo = VideoRepository(db)
    search_repo = UserSearchHistoryRepository(db)
    return SearchService(video_repo, search_repo)

# ====== SEARCH ENDPOINTS ======

@router.post("/")
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


@router.post("/click")
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
