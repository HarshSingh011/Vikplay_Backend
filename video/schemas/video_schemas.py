"""
Video schemas for request/response models
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Video schemas
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

# Category schemas
class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass

class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    created_at: datetime
    video_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# User preferences schemas
class UserPreferencesBase(BaseModel):
    """Base user preferences schema"""
    preferred_categories: Optional[List[int]] = []
    preferred_tags: Optional[List[str]] = []
    language_preference: str = "en"
    content_rating_preference: str = "G"
    recommendation_settings: Optional[Dict[str, Any]] = {}

class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences"""
    pass

class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# History and progress schemas
class WatchProgressUpdate(BaseModel):
    """Schema for updating watch progress"""
    user_id: int
    video_id: int
    position: int = Field(..., ge=0)
    duration: int = Field(..., ge=0)

class VideoRating(BaseModel):
    """Schema for video rating"""
    user_id: int
    video_id: int
    rating: float = Field(..., ge=1.0, le=5.0)

class UserVideoHistoryResponse(BaseModel):
    """Schema for user video history response"""
    id: int
    user_id: int
    video_id: int
    watched_at: datetime
    watch_duration: int
    completed: bool
    last_position: int
    rating: Optional[float] = None
    
    class Config:
        from_attributes = True
