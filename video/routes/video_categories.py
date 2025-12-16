"""
Video Category Routes - Category management
Handles video category operations
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import VideoService
from video.repositories.video_repository import VideoRepository, CategoryRepository
from video.schemas.video_schemas import (
    CategoryCreate, CategoryResponse, VideoResponse, CategoryCreateWithAuth
)

router = APIRouter(prefix="/categories")

# ====== DEPENDENCY INJECTION ======

def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    """Dependency injection for VideoService"""
    video_repo = VideoRepository(db)
    category_repo = CategoryRepository(db)
    return VideoService(video_repo, category_repo)

# ====== CATEGORY ENDPOINTS ======

@router.post("/", response_model=CategoryResponse)
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


@router.get("/", response_model=List[CategoryResponse])
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


@router.get("/{category_id}/videos", response_model=List[VideoResponse])
async def get_videos_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 20,
    video_service: VideoService = Depends(get_video_service)
):
    """Get videos by category"""
    return await video_service.get_videos_by_category(category_id, skip, limit)
