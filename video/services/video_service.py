"""
Video Service - Business logic layer for video operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from video.repositories.video_repository import (
    VideoRepository, 
    CategoryRepository, 
    UserHistoryRepository,
    UserPreferencesRepository
)
from video.schemas import (
    VideoCreate, 
    VideoUpdate, 
    UserVideoHistoryCreate,
    UserPreferencesCreate,
    VideoRecommendationRequest
)
from models.models import Video, Category, UserVideoHistory, UserPreferences

class VideoService:
    """Service layer for video-related business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.category_repo = CategoryRepository(db)
        self.history_repo = UserHistoryRepository(db)
        self.preferences_repo = UserPreferencesRepository(db)
    
    def create_video(self, video_data: VideoCreate) -> Video:
        """Create a new video"""
        return self.video_repo.create_video(video_data.model_dump())
    
    def get_video(self, video_id: int, user_id: Optional[str] = None) -> Optional[Video]:
        """Get video by ID and optionally record view"""
        video = self.video_repo.get_video_by_id(video_id)
        if video and user_id:
            # Record that user viewed this video
            self.history_repo.add_to_history(user_id, video_id)
            # Increment view count
            self.video_repo.increment_view_count(video_id)
        return video
    
    def update_video(self, video_id: int, video_data: VideoUpdate) -> Optional[Video]:
        """Update video information"""
        update_dict = {k: v for k, v in video_data.model_dump().items() if v is not None}
        return self.video_repo.update_video(video_id, update_dict)
    
    def delete_video(self, video_id: int) -> bool:
        """Delete video"""
        return self.video_repo.delete_video(video_id)
    
    def get_videos(self, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[Video]:
        """Get videos with pagination and optional category filter"""
        return self.video_repo.get_videos(skip, limit, category_id)
    
    def search_videos(self, query: str, limit: int = 20) -> List[Video]:
        """Search videos"""
        return self.video_repo.search_videos(query, limit)
    
    def get_popular_videos(self, limit: int = 10) -> List[Video]:
        """Get popular videos"""
        return self.video_repo.get_popular_videos(limit)
    
    def record_watch_progress(self, user_id: str, history_data: UserVideoHistoryCreate) -> UserVideoHistory:
        """Record user's watch progress"""
        return self.history_repo.add_to_history(
            user_id=user_id,
            video_id=history_data.video_id,
            watch_duration=history_data.watch_duration,
            completion_percentage=history_data.completion_percentage
        )
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[UserVideoHistory]:
        """Get user's watch history"""
        return self.history_repo.get_user_history(user_id, limit)
    
    def get_recently_watched(self, user_id: str, days: int = 7, limit: int = 10) -> List[Video]:
        """Get user's recently watched videos"""
        return self.history_repo.get_recently_watched(user_id, days, limit)
    
    def rate_video(self, user_id: str, video_id: int, rating: int) -> Optional[UserVideoHistory]:
        """Rate a video"""
        return self.history_repo.rate_video(user_id, video_id, rating)
    
    def like_video(self, user_id: str, video_id: int, liked: bool) -> Optional[UserVideoHistory]:
        """Like or dislike a video"""
        return self.history_repo.like_video(user_id, video_id, liked)
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        return self.preferences_repo.get_user_preferences(user_id)
    
    def update_user_preferences(self, user_id: str, preferences: UserPreferencesCreate) -> UserPreferences:
        """Update user preferences"""
        prefs_dict = preferences.model_dump(exclude_unset=True)
        
        # Convert list fields to JSON strings
        if 'preferred_categories' in prefs_dict and prefs_dict['preferred_categories']:
            prefs_dict['preferred_categories'] = json.dumps(prefs_dict['preferred_categories'])
        if 'disliked_categories' in prefs_dict and prefs_dict['disliked_categories']:
            prefs_dict['disliked_categories'] = json.dumps(prefs_dict['disliked_categories'])
        
        return self.preferences_repo.create_or_update_preferences(user_id, prefs_dict)
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user's viewing analytics"""
        history = self.history_repo.get_user_history(user_id, limit=1000)
        favorite_categories = self.history_repo.get_user_favorite_categories(user_id)
        
        total_watch_time = sum([h.watch_duration for h in history])
        total_videos_watched = len(history)
        avg_completion = sum([h.completion_percentage for h in history]) / len(history) if history else 0
        
        return {
            "total_watch_time_seconds": total_watch_time,
            "total_videos_watched": total_videos_watched,
            "average_completion_percentage": avg_completion,
            "favorite_categories": favorite_categories,
            "recent_activity": len([h for h in history if h.watched_at > datetime.utcnow() - timedelta(days=7)])
        }
    
    # Category related methods
    def create_category(self, name: str, description: str = None) -> Category:
        """Create a new category"""
        return self.category_repo.create_category(name, description)
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        return self.category_repo.get_all_categories()
    
    def get_category(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return self.category_repo.get_category_by_id(category_id)
    
    def get_videos_by_category(self, category_id: int, limit: int = 10) -> List[Video]:
        """Get videos from specific category"""
        return self.video_repo.get_videos_by_category(category_id, limit)
