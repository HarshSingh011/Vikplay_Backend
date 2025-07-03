"""
Video core schemas for the VikPay Backend
Request/Response models for video operations
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class VideoBase(BaseModel):
    """Base video schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_public: bool = True


class VideoCreate(VideoBase):
    """Schema for creating a video"""
    filename: str
    file_path: str
    user_id: Optional[int] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    thumbnail_path: Optional[str] = None


class VideoUpdate(BaseModel):
    """Schema for updating a video"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_public: Optional[bool] = None
    thumbnail_path: Optional[str] = None


class VideoResponse(VideoBase):
    """Schema for video response"""
    id: int
    filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    user_id: Optional[int] = None
    view_count: int = 0
    like_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VideoRating(BaseModel):
    """Schema for video rating"""
    user_id: int
    video_id: int
    rating: float = Field(..., ge=1.0, le=5.0)


class VideoAnalytics(BaseModel):
    """Video performance analytics"""
    video_id: int
    total_views: int
    unique_viewers: int
    average_watch_time: float
    completion_rate: float
    engagement_rate: float  # likes + shares / views
    retention_curve: List[float]  # retention at different time points
    popular_search_terms: List[str]  # terms that led to this video
