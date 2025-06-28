"""
Video Routes - API endpoints for video management with AI integration
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
from datetime import datetime

from database import get_db
from auth.utils.jwt_token import get_current_user
from video.services.video_service import VideoService
from video.schemas import (
    VideoCreate, VideoUpdate, VideoResponse, 
    CategoryCreate, CategoryResponse,
    UserVideoHistoryCreate, UserVideoHistoryResponse,
    VideoRating, VideoLikeDislike,
    UserPreferencesCreate, UserPreferencesResponse
)
from ai.services.recommendation_service import VideoRecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["Videos"])

# Video CRUD Operations
@router.post("/", response_model=VideoResponse)
async def create_video(
    video: VideoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new video"""
    try:
        video_service = VideoService(db)
        new_video = video_service.create_video(video)
        
        # Initialize AI embeddings for the new video
        try:
            recommendation_service = VideoRecommendationService(db)
            recommendation_service.initialize_embeddings_for_video(new_video)
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings for video {new_video.id}: {str(e)}")
        
        return new_video
        
    except Exception as e:
        logger.error(f"Failed to create video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get video by ID and record view history"""
    try:
        video_service = VideoService(db)
        video = video_service.get_video(video_id, user_id=current_user["user_id"])
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get video: {str(e)}")

@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update video information"""
    try:
        video_service = VideoService(db)
        updated_video = video_service.update_video(video_id, video_update)
        
        if not updated_video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Update AI embeddings
        try:
            recommendation_service = VideoRecommendationService(db)
            recommendation_service.initialize_embeddings_for_video(updated_video)
        except Exception as e:
            logger.warning(f"Failed to update embeddings for video {video_id}: {str(e)}")
        
        return updated_video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update video: {str(e)}")

@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete video"""
    try:
        video_service = VideoService(db)
        success = video_service.delete_video(video_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {"success": True, "message": f"Video {video_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")

@router.get("/", response_model=List[VideoResponse])
async def get_videos(
    skip: int = Query(0, ge=0, description="Number of videos to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of videos to return"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    db: Session = Depends(get_db)
):
    """Get videos with pagination and optional category filter"""
    try:
        video_service = VideoService(db)
        videos = video_service.get_videos(skip=skip, limit=limit, category_id=category_id)
        return videos
        
    except Exception as e:
        logger.error(f"Failed to get videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get videos: {str(e)}")

@router.get("/search/")
async def search_videos(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Search videos by title, description, or tags"""
    try:
        video_service = VideoService(db)
        videos = video_service.search_videos(query, limit)
        return {"videos": videos, "query": query, "total": len(videos)}
        
    except Exception as e:
        logger.error(f"Failed to search videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search videos: {str(e)}")

@router.get("/popular/")
async def get_popular_videos(
    limit: int = Query(10, ge=1, le=50, description="Number of popular videos"),
    db: Session = Depends(get_db)
):
    """Get popular videos by view count"""
    try:
        video_service = VideoService(db)
        videos = video_service.get_popular_videos(limit)
        return {"videos": videos, "total": len(videos)}
        
    except Exception as e:
        logger.error(f"Failed to get popular videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular videos: {str(e)}")

# User History and Interaction
@router.post("/history/", response_model=UserVideoHistoryResponse)
async def record_watch_progress(
    history_data: UserVideoHistoryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record user's video watch progress"""
    try:
        video_service = VideoService(db)
        history_entry = video_service.record_watch_progress(
            user_id=current_user["user_id"],
            history_data=history_data
        )
        return history_entry
        
    except Exception as e:
        logger.error(f"Failed to record watch progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record watch progress: {str(e)}")

@router.get("/history/", response_model=List[UserVideoHistoryResponse])
async def get_user_watch_history(
    limit: int = Query(50, ge=1, le=200, description="Number of history entries"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's video watch history"""
    try:
        video_service = VideoService(db)
        history = video_service.get_user_history(current_user["user_id"], limit)
        return history
        
    except Exception as e:
        logger.error(f"Failed to get user history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user history: {str(e)}")

@router.get("/recently-watched/")
async def get_recently_watched(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of videos"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recently watched videos"""
    try:
        video_service = VideoService(db)
        videos = video_service.get_recently_watched(current_user["user_id"], days, limit)
        return {"videos": videos, "days": days, "total": len(videos)}
        
    except Exception as e:
        logger.error(f"Failed to get recently watched: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recently watched: {str(e)}")

@router.post("/{video_id}/rate")
async def rate_video(
    video_id: int,
    rating_data: VideoRating,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate a video (1-5 stars)"""
    try:
        video_service = VideoService(db)
        history_entry = video_service.rate_video(
            user_id=current_user["user_id"],
            video_id=video_id,
            rating=rating_data.rating
        )
        
        if not history_entry:
            raise HTTPException(status_code=404, detail="Video not found in user's history")
        
        return {"success": True, "rating": rating_data.rating, "video_id": video_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rate video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rate video: {str(e)}")

@router.post("/{video_id}/like")
async def like_video(
    video_id: int,
    like_data: VideoLikeDislike,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Like or dislike a video"""
    try:
        video_service = VideoService(db)
        history_entry = video_service.like_video(
            user_id=current_user["user_id"],
            video_id=video_id,
            liked=like_data.liked
        )
        
        if not history_entry:
            raise HTTPException(status_code=404, detail="Video not found in user's history")
        
        action = "liked" if like_data.liked else "disliked"
        return {"success": True, "action": action, "video_id": video_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to like/dislike video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to like/dislike video: {str(e)}")

# User Preferences
@router.get("/preferences/", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's video preferences"""
    try:
        video_service = VideoService(db)
        preferences = video_service.get_user_preferences(current_user["user_id"])
        
        if not preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user preferences: {str(e)}")

@router.post("/preferences/", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences: UserPreferencesCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's video preferences"""
    try:
        video_service = VideoService(db)
        updated_preferences = video_service.update_user_preferences(
            user_id=current_user["user_id"],
            preferences=preferences
        )
        return updated_preferences
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {str(e)}")

# Analytics
@router.get("/analytics/")
async def get_user_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's viewing analytics"""
    try:
        video_service = VideoService(db)
        analytics = video_service.get_user_analytics(current_user["user_id"])
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")

# Category Management
@router.post("/categories/", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new video category"""
    try:
        video_service = VideoService(db)
        new_category = video_service.create_category(category.name, category.description)
        return new_category
        
    except Exception as e:
        logger.error(f"Failed to create category: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")

@router.get("/categories/", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all video categories"""
    try:
        video_service = VideoService(db)
        categories = video_service.get_all_categories()
        return categories
        
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/categories/{category_id}/videos")
async def get_videos_by_category(
    category_id: int,
    limit: int = Query(20, ge=1, le=100, description="Number of videos"),
    db: Session = Depends(get_db)
):
    """Get videos from a specific category"""
    try:
        video_service = VideoService(db)
        category = video_service.get_category(category_id)
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        videos = video_service.get_videos_by_category(category_id, limit)
        return {
            "category": category,
            "videos": videos,
            "total": len(videos)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get videos by category: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get videos by category: {str(e)}")
