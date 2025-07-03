"""
Analytics and tracking schemas for the VikPay Backend
Request/Response models for automatic data collection
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


# 1. VIEWING HISTORY TRACKING (Enhanced)
class WatchProgressUpdate(BaseModel):
    """Schema for updating watch progress"""
    user_id: int
    video_id: int
    position: int = Field(..., ge=0)
    duration: int = Field(..., ge=0)


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
