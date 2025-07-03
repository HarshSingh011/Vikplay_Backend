"""
Video CRUD Routes - Basic video operations
Clean architecture implementation with dependency injection
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import VideoService
from video.repositories.video_repository import VideoRepository, CategoryRepository
from video.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse, VideoCreateWithAuth, 
    VideoUpdateWithAuth, VideoDeleteWithAuth
)

router = APIRouter(prefix="/videos", tags=["videos"])

# ====== DEPENDENCY INJECTION ======

def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    """Dependency injection for VideoService"""
    video_repo = VideoRepository(db)
    category_repo = CategoryRepository(db)
    return VideoService(video_repo, category_repo)

# ====== VIDEO CRUD OPERATIONS ======

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
    """Get popular videos (public endpoint)"""
    return await video_service.get_popular_videos(limit)


@router.get("/trending/", response_model=List[VideoResponse])
async def get_trending_videos(
    days: int = 7,
    limit: int = 20,
    video_service: VideoService = Depends(get_video_service)
):
    """Get trending videos (public endpoint)"""
    return await video_service.get_trending_videos(days, limit)
