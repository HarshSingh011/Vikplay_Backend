"""
Video Schemas - Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    duration: Optional[float] = Field(None, ge=0)
    tags: Optional[str] = Field(None, max_length=500)

class VideoCreate(VideoBase):
    file_url: str = Field(..., min_length=1)

class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    duration: Optional[float] = Field(None, ge=0)
    tags: Optional[str] = Field(None, max_length=500)

class VideoResponse(VideoBase):
    id: int
    file_url: str
    view_count: int = 0
    created_at: datetime
    category: Optional[dict] = None

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class UserVideoHistoryCreate(BaseModel):
    video_id: int
    watch_duration: float = Field(0.0, ge=0)
    completion_percentage: float = Field(0.0, ge=0, le=100)

class UserVideoHistoryResponse(BaseModel):
    id: int
    user_id: str
    video_id: int
    watched_at: datetime
    watch_duration: float
    completion_percentage: float
    rating: Optional[int] = None
    liked: Optional[bool] = None
    video: Optional[VideoResponse] = None

    class Config:
        from_attributes = True

class VideoRating(BaseModel):
    rating: int = Field(..., ge=1, le=5)

class VideoLikeDislike(BaseModel):
    liked: bool

class UserPreferencesCreate(BaseModel):
    preferred_categories: Optional[List[int]] = None
    disliked_categories: Optional[List[int]] = None
    preferred_duration_min: Optional[float] = Field(None, ge=0)
    preferred_duration_max: Optional[float] = Field(None, ge=0)

class UserPreferencesResponse(BaseModel):
    id: int
    user_id: str
    preferred_categories: Optional[str] = None
    disliked_categories: Optional[str] = None
    preferred_duration_min: Optional[float] = None
    preferred_duration_max: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VideoRecommendationRequest(BaseModel):
    limit: int = Field(10, ge=1, le=50)
    exclude_watched: bool = True
    category_id: Optional[int] = None

class VideoRecommendationResponse(BaseModel):
    videos: List[VideoResponse]
    recommendation_reason: str
    confidence_score: float = Field(..., ge=0, le=1)
