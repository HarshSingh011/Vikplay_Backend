"""
Video schemas for the VikPay Backend
Request/Response models for automatic data collection
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
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


# ====== AUTOMATIC COLLECTION SCHEMAS ======

# 1. VIEWING HISTORY TRACKING (Enhanced)
class WatchProgressUpdateEnhanced(BaseModel):
    """
    AUTOMATIC COLLECTION: Enhanced Viewing History
    Sent automatically when user watches video
    """
    video_id: int
    watch_duration: int  # seconds watched in this session
    completion_percentage: float  # current % of video completed
    device_type: Optional[str] = None
    session_id: Optional[str] = None


class VideoEngagement(BaseModel):
    """
    AUTOMATIC COLLECTION: Engagement Metrics
    Sent when user interacts with video
    """
    video_id: int
    rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 stars
    liked: Optional[bool] = None  # True=like, False=dislike
    shared: bool = False
    bookmarked: bool = False


class VideoInteraction(BaseModel):
    """
    AUTOMATIC COLLECTION: Detailed Engagement
    Tracks every user interaction
    """
    video_id: int
    interaction_type: str  # play, pause, seek, like, share, comment, etc.
    interaction_value: Optional[str] = None  # specific value
    video_timestamp: Optional[int] = None  # where in video
    session_id: Optional[str] = None
    device_type: Optional[str] = None


# 2. SEARCH QUERY TRACKING
class SearchQueryLog(BaseModel):
    """
    AUTOMATIC COLLECTION: Search Queries
    Logged automatically when user searches
    """
    search_query: str = Field(..., max_length=500)
    search_filters: Optional[Dict[str, Any]] = None
    device_type: Optional[str] = None


class SearchResultClick(BaseModel):
    """
    AUTOMATIC COLLECTION: Search Interaction
    Logged when user clicks search result
    """
    search_id: int  # ID of the search query
    clicked_video_id: int
    click_position: int  # position in search results
    time_to_click: Optional[float] = None  # seconds from search to click


# 3. SESSION PATTERN TRACKING
class SessionStart(BaseModel):
    """
    AUTOMATIC COLLECTION: Session Patterns
    Logged when user starts session
    """
    session_id: str
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    user_agent: Optional[str] = None


class SessionActivity(BaseModel):
    """
    AUTOMATIC COLLECTION: Session Activity
    Updated throughout session
    """
    session_id: str
    videos_watched: int = 0
    searches_performed: int = 0
    videos_liked: int = 0
    videos_shared: int = 0


class SessionEnd(BaseModel):
    """
    AUTOMATIC COLLECTION: Session End
    Logged when session ends
    """
    session_id: str
    session_duration: int  # total seconds


# RESPONSE SCHEMAS FOR ANALYTICS
class UserSearchHistoryResponse(BaseModel):
    id: int
    search_query: str
    searched_at: datetime
    results_count: int
    clicked_video_id: Optional[int] = None
    click_position: Optional[int] = None

    class Config:
        from_attributes = True


class UserSessionResponse(BaseModel):
    id: int
    session_id: str
    session_start: datetime
    session_end: Optional[datetime] = None
    session_duration: Optional[int] = None
    videos_watched: int
    searches_performed: int
    device_type: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None

    class Config:
        from_attributes = True


# USER PREFERENCES
class UserPreferencesUpdate(BaseModel):
    """User can explicitly set these preferences"""
    preferred_categories: Optional[List[str]] = None
    disliked_categories: Optional[List[str]] = None
    preferred_duration_min: Optional[int] = None
    preferred_duration_max: Optional[int] = None
    preferred_languages: Optional[List[str]] = None
    content_rating_preference: Optional[str] = None
    mature_content_allowed: Optional[bool] = None
    violence_filter: Optional[bool] = None
    profanity_filter: Optional[bool] = None


# ANALYTICS SCHEMAS
class UserAnalytics(BaseModel):
    """Comprehensive user analytics for AI"""
    total_videos_watched: int
    total_watch_time: int  # seconds
    average_completion_rate: float
    favorite_categories: List[Dict[str, Union[str, int]]]  # [{"category": "tech", "count": 10}]
    most_active_times: List[str]  # ["evening", "weekend"]
    preferred_video_length: int  # average preferred duration
    engagement_score: float  # overall user engagement
    recent_interests: List[str]  # recent category interests


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
