"""
Video Repository - Data access layer for video operations and user history
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta
import json

from models.models import Video, Category, UserVideoHistory, UserPreferences

class VideoRepository:
    """Repository for video-related database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_video(self, video_data: dict) -> Video:
        """Create a new video record"""
        db_video = Video(**video_data)
        self.db.add(db_video)
        self.db.commit()
        self.db.refresh(db_video)
        return db_video
    
    def get_video_by_id(self, video_id: int) -> Optional[Video]:
        """Get video by ID"""
        return self.db.query(Video).filter(Video.id == video_id).first()
    
    def get_videos(self, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[Video]:
        """Get videos with optional category filter"""
        query = self.db.query(Video)
        
        if category_id is not None:
            query = query.filter(Video.category_id == category_id)
        
        return query.order_by(desc(Video.created_at)).offset(skip).limit(limit).all()
    
    def get_popular_videos(self, limit: int = 10) -> List[Video]:
        """Get most popular videos by view count"""
        return self.db.query(Video).order_by(desc(Video.view_count)).limit(limit).all()
    
    def get_videos_by_category(self, category_id: int, limit: int = 10) -> List[Video]:
        """Get videos from specific category"""
        return (self.db.query(Video)
                .filter(Video.category_id == category_id)
                .order_by(desc(Video.view_count))
                .limit(limit)
                .all())
    
    def increment_view_count(self, video_id: int):
        """Increment view count for a video"""
        video = self.get_video_by_id(video_id)
        if video:
            video.view_count = video.view_count + 1
            self.db.commit()
    
    def delete_video(self, video_id: int) -> bool:
        """Delete video by ID"""
        video = self.get_video_by_id(video_id)
        if video:
            self.db.delete(video)
            self.db.commit()
            return True
        return False
    
    def update_video(self, video_id: int, update_data: dict) -> Optional[Video]:
        """Update video information"""
        video = self.get_video_by_id(video_id)
        if video:
            for key, value in update_data.items():
                setattr(video, key, value)
            self.db.commit()
            self.db.refresh(video)
            return video
        return None
    
    def search_videos(self, query: str, limit: int = 20) -> List[Video]:
        """Search videos by title or description"""
        search_term = f"%{query}%"
        return (self.db.query(Video)
                .filter(
                    (Video.title.ilike(search_term)) | 
                    (Video.description.ilike(search_term)) |
                    (Video.tags.ilike(search_term))
                )
                .order_by(desc(Video.view_count))
                .limit(limit)
                .all())

class CategoryRepository:
    """Repository for category-related database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_category(self, name: str, description: str = None) -> Category:
        """Create a new category"""
        db_category = Category(name=name, description=description)
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name (case insensitive)"""
        return self.db.query(Category).filter(Category.name.ilike(name)).first()
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        return self.db.query(Category).all()
    
    def get_or_create_category(self, name: str, description: str = None) -> Category:
        """Get existing category or create new one"""
        category = self.get_category_by_name(name)
        if not category:
            category = self.create_category(name, description or f"Videos about {name}")
        return category

class UserHistoryRepository:
    """Repository for user video history operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_to_history(self, user_id: str, video_id: int, watch_duration: float = 0.0, 
                      completion_percentage: float = 0.0) -> UserVideoHistory:
        """Add or update user's video watch history"""
        # Check if history entry already exists
        existing_history = (self.db.query(UserVideoHistory)
                          .filter(and_(UserVideoHistory.user_id == user_id, 
                                     UserVideoHistory.video_id == video_id))
                          .first())
        
        if existing_history:
            # Update existing entry
            existing_history.watched_at = datetime.utcnow()
            existing_history.watch_duration = max(existing_history.watch_duration, watch_duration)
            existing_history.completion_percentage = max(existing_history.completion_percentage, completion_percentage)
            self.db.commit()
            self.db.refresh(existing_history)
            return existing_history
        else:
            # Create new entry
            history_entry = UserVideoHistory(
                user_id=user_id,
                video_id=video_id,
                watch_duration=watch_duration,
                completion_percentage=completion_percentage
            )
            self.db.add(history_entry)
            self.db.commit()
            self.db.refresh(history_entry)
            return history_entry
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[UserVideoHistory]:
        """Get user's video watch history"""
        return (self.db.query(UserVideoHistory)
                .filter(UserVideoHistory.user_id == user_id)
                .order_by(desc(UserVideoHistory.watched_at))
                .limit(limit)
                .all())
    
    def get_recently_watched(self, user_id: str, days: int = 7, limit: int = 10) -> List[Video]:
        """Get recently watched videos"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        return (self.db.query(Video)
                .join(UserVideoHistory)
                .filter(
                    UserVideoHistory.user_id == user_id,
                    UserVideoHistory.watched_at >= since_date
                )
                .order_by(desc(UserVideoHistory.watched_at))
                .limit(limit)
                .all())
    
    def get_user_favorite_categories(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's most watched categories"""
        results = (self.db.query(
                    Category.id,
                    Category.name,
                    func.count(UserVideoHistory.id).label('watch_count')
                )
                .join(Video, Video.category_id == Category.id)
                .join(UserVideoHistory, UserVideoHistory.video_id == Video.id)
                .filter(UserVideoHistory.user_id == user_id)
                .group_by(Category.id, Category.name)
                .order_by(desc('watch_count'))
                .limit(limit)
                .all())
        
        return [{"category_id": r.id, "category_name": r.name, "watch_count": r.watch_count} 
                for r in results]
    
    def rate_video(self, user_id: str, video_id: int, rating: int) -> Optional[UserVideoHistory]:
        """Rate a video (1-5 stars)"""
        if rating < 1 or rating > 5:
            return None
            
        history_entry = (self.db.query(UserVideoHistory)
                        .filter(and_(UserVideoHistory.user_id == user_id,
                                   UserVideoHistory.video_id == video_id))
                        .first())
        
        if history_entry:
            history_entry.rating = rating
            self.db.commit()
            self.db.refresh(history_entry)
            return history_entry
        return None
    
    def like_video(self, user_id: str, video_id: int, liked: bool) -> Optional[UserVideoHistory]:
        """Like or dislike a video"""
        history_entry = (self.db.query(UserVideoHistory)
                        .filter(and_(UserVideoHistory.user_id == user_id,
                                   UserVideoHistory.video_id == video_id))
                        .first())
        
        if history_entry:
            history_entry.liked = liked
            self.db.commit()
            self.db.refresh(history_entry)
            return history_entry
        return None

class UserPreferencesRepository:
    """Repository for user preferences operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        return self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    
    def create_or_update_preferences(self, user_id: str, preferences_data: dict) -> UserPreferences:
        """Create or update user preferences"""
        preferences = self.get_user_preferences(user_id)
        
        if preferences:
            # Update existing preferences
            for key, value in preferences_data.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
            preferences.updated_at = datetime.utcnow()
        else:
            # Create new preferences
            preferences = UserPreferences(user_id=user_id, **preferences_data)
            self.db.add(preferences)
        
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
    
    def update_preferred_categories(self, user_id: str, category_ids: List[int]):
        """Update user's preferred categories"""
        preferences_data = {"preferred_categories": json.dumps(category_ids)}
        return self.create_or_update_preferences(user_id, preferences_data)
    
    def update_duration_preferences(self, user_id: str, min_duration: float, max_duration: float):
        """Update user's preferred video duration range"""
        preferences_data = {
            "preferred_duration_min": min_duration,
            "preferred_duration_max": max_duration
        }
        return self.create_or_update_preferences(user_id, preferences_data)
