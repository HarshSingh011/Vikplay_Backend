import os
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from video.models import Video, Category
from video.schemas import VideoCreate, Video as VideoResponse, Category as CategoryResponse
from video.services import VideoService, CategoryService

router = APIRouter(
    prefix="/videos",
    tags=["videos"]
)

@router.post("/", response_model=VideoResponse)
async def upload_video(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a new video with required category selection (by name)
    """
    video_service = VideoService(db)
    return await video_service.upload_video(title, description, category, file)

@router.get("/", response_model=List[VideoResponse])
def get_videos(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all videos with optional category filter
    """
    video_service = VideoService(db)
    return video_service.get_videos(skip, limit, category_id)

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all available categories
    """
    video_service = VideoService(db)
    return video_service.get_categories()

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """
    Get a specific video by ID
    """
    video_service = VideoService(db)
    return video_service.get_video_by_id(video_id)

@router.delete("/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """
    Delete a video by ID
    """
    video_service = VideoService(db)
    return video_service.delete_video(video_id)
