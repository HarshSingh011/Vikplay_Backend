"""
Video Repository Layer - Clean Architecture Data Access Layer
Handles all database operations for video-related entities with improved structure
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from abc import ABC, abstractmethod

from video.models.video_models import (
    Video, Category, UserVideoHistory, UserSearchHistory, 
    UserSession, UserPreferences, VideoInteractionLog
)


# Abstract Base Repository Interface
class IRepository(ABC):
    """Interface for repository pattern"""
    
    @abstractmethod
    def create(self, obj_data: dict) -> Any: pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[Any]: pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]: pass
    
    @abstractmethod
    def update(self, entity_id: int, update_data: dict) -> Optional[Any]: pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool: pass


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class
    
    def create(self, **kwargs) -> Any:
        """Create a new entity"""
        entity = self.model_class(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        """Get entity by ID"""
        return self.db.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities with pagination"""
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    def update(self, entity_id: int, **kwargs) -> Optional[Any]:
        """Update entity by ID"""
        entity = self.get_by_id(entity_id)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.db.commit()
            self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False


class VideoRepository(BaseRepository):
    """Repository for Video operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Video)
    
    def get_by_category(self, category_id: int, skip: int = 0, limit: int = 20) -> List[Video]:
        """Get videos by category with pagination"""
        return self.db.query(Video).filter(
            Video.category_id == category_id
        ).offset(skip).limit(limit).all()
    
    def search_videos(self, query: str, filters: Optional[Dict] = None, 
                     skip: int = 0, limit: int = 20) -> List[Video]:
        """Search videos with filters"""
        query_builder = self.db.query(Video)
        
        # Text search
        if query:
            query_builder = query_builder.filter(
                or_(
                    Video.title.ilike(f"%{query}%"),
                    Video.description.ilike(f"%{query}%"),
                    Video.tags.op('?')(query.lower())  # JSON contains
                )
            )
        
        # Apply filters
        if filters:
            if filters.get("category_id"):
                query_builder = query_builder.filter(
                    Video.category_id == filters["category_id"]
                )
            
            if filters.get("language"):
                query_builder = query_builder.filter(
                    Video.language == filters["language"]
                )
            
            if filters.get("content_rating"):
                query_builder = query_builder.filter(
                    Video.content_rating == filters["content_rating"]
                )
            
            if filters.get("min_duration"):
                query_builder = query_builder.filter(
                    Video.duration >= filters["min_duration"]
                )
            
            if filters.get("max_duration"):
                query_builder = query_builder.filter(
                    Video.duration <= filters["max_duration"]
                )
        
        return query_builder.offset(skip).limit(limit).all()
    
    def get_popular_videos(self, limit: int = 20) -> List[Video]:
        """Get popular videos based on engagement metrics"""
        return self.db.query(Video).order_by(
            desc(Video.engagement_score),
            desc(Video.view_count)
        ).limit(limit).all()
    
    def get_videos_by_category(self, category_id: int, 
                              skip: int = 0, limit: int = 20) -> List[Video]:
        """Get videos by category"""
        return self.db.query(Video).filter(
            Video.category_id == category_id
        ).offset(skip).limit(limit).all()
    
    def update_video_metrics(self, video_id: int, metrics: Dict[str, Any]) -> bool:
        """Update video engagement metrics"""
        video = self.get_by_id(video_id)
        if video:
            for key, value in metrics.items():
                if hasattr(video, key):
                    setattr(video, key, value)
            video.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False


class CategoryRepository(BaseRepository):
    """Repository for Category operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Category)
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        return self.db.query(Category).filter(
            Category.name.ilike(name)
        ).first()
    
    def get_categories_with_video_count(self) -> List[Dict]:
        """Get categories with their video counts"""
        try:
            result = self.db.query(
                Category.id,
                Category.name,
                Category.description,
                Category.created_at,
                func.count(Video.id).label('video_count')
            ).outerjoin(Video).group_by(
                Category.id, Category.name, Category.description, Category.created_at
            ).all()
            
            # Convert SQLAlchemy row objects to dictionaries
            return [
                {
                    'id': row.id,
                    'name': row.name,
                    'description': row.description,
                    'created_at': row.created_at,
                    'video_count': row.video_count
                }
                for row in result
            ]
        except Exception as e:
            # Return empty list if there's an error (like missing tables)
            return []


class UserVideoHistoryRepository(BaseRepository):
    """Repository for user video history operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserVideoHistory)
    
    def get_user_history(self, user_id: int, skip: int = 0, 
                        limit: int = 50) -> List[UserVideoHistory]:
        """Get user's video watching history"""
        return self.db.query(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).order_by(desc(UserVideoHistory.watched_at)).offset(skip).limit(limit).all()
    
    def get_user_video_progress(self, user_id: int, video_id: int) -> Optional[UserVideoHistory]:
        """Get user's progress for a specific video"""
        return self.db.query(UserVideoHistory).filter(
            and_(
                UserVideoHistory.user_id == user_id,
                UserVideoHistory.video_id == video_id
            )
        ).order_by(desc(UserVideoHistory.watched_at)).first()
    
    def record_watch_progress(self, user_id: int, video_id: int, 
                            watch_data: Dict[str, Any]) -> UserVideoHistory:
        """Record or update user's watch progress"""
        existing = self.get_user_video_progress(user_id, video_id)
        
        if existing and existing.session_id == watch_data.get("session_id"):
            # Update existing record for same session
            for key, value in watch_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new record
            return self.create(
                user_id=user_id,
                video_id=video_id,
                **watch_data
            )
    
    def get_user_engagement_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's engagement statistics"""
        history = self.db.query(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).all()
        
        if not history:
            return {
                "total_videos_watched": 0,
                "total_watch_time": 0,
                "average_completion_rate": 0.0,
                "videos_liked": 0,
                "videos_rated": 0
            }
        
        total_videos = len(history)
        total_watch_time = sum(h.watch_duration for h in history)
        avg_completion = sum(h.completion_percentage for h in history) / total_videos
        videos_liked = len([h for h in history if h.liked is True])
        videos_rated = len([h for h in history if h.rating is not None])
        
        return {
            "total_videos_watched": total_videos,
            "total_watch_time": total_watch_time,
            "average_completion_rate": avg_completion,
            "videos_liked": videos_liked,
            "videos_rated": videos_rated
        }


class UserSearchHistoryRepository(BaseRepository):
    """Repository for user search history operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserSearchHistory)
    
    def record_search(self, user_id: int, search_data: Dict[str, Any]) -> UserSearchHistory:
        """Record a user's search query"""
        return self.create(user_id=user_id, **search_data)
    
    def update_search_click(self, search_id: int, click_data: Dict[str, Any]) -> bool:
        """Update search record with click information"""
        search_record = self.get_by_id(search_id)
        if search_record:
            for key, value in click_data.items():
                if hasattr(search_record, key):
                    setattr(search_record, key, value)
            self.db.commit()
            return True
        return False
    
    def get_user_search_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze user's search patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        searches = self.db.query(UserSearchHistory).filter(
            and_(
                UserSearchHistory.user_id == user_id,
                UserSearchHistory.searched_at >= cutoff_date
            )
        ).all()
        
        if not searches:
            return {
                "total_searches": 0,
                "unique_queries": 0,
                "click_through_rate": 0.0,
                "common_terms": []
            }
        
        total_searches = len(searches)
        unique_queries = len(set(s.search_query.lower() for s in searches))
        clicked_searches = len([s for s in searches if s.clicked_video_id is not None])
        click_through_rate = clicked_searches / total_searches if total_searches > 0 else 0
        
        # Extract common search terms
        all_terms = []
        for search in searches:
            terms = search.search_query.lower().split()
            all_terms.extend([term for term in terms if len(term) > 2])
        
        # Count term frequency
        term_counts = {}
        for term in all_terms:
            term_counts[term] = term_counts.get(term, 0) + 1
        
        common_terms = sorted(term_counts.items(), 
                            key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_searches": total_searches,
            "unique_queries": unique_queries,
            "click_through_rate": click_through_rate,
            "common_terms": [{"term": term, "count": count} for term, count in common_terms]
        }


class UserSessionRepository(BaseRepository):
    """Repository for user session operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserSession)
    
    def start_session(self, user_id: int, session_data: Dict[str, Any]) -> UserSession:
        """Start a new user session"""
        return self.create(user_id=user_id, **session_data)
    
    def update_session_activity(self, session_id: str, activity_data: Dict[str, Any]) -> bool:
        """Update session activity"""
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            for key, value in activity_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            self.db.commit()
            return True
        return False
    
    def end_session(self, session_id: str, end_data: Dict[str, Any]) -> bool:
        """End a user session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            session.session_end = datetime.utcnow()
            for key, value in end_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            self.db.commit()
            return True
        return False
    
    def get_user_session_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze user's session patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.session_start >= cutoff_date
            )
        ).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "average_session_duration": 0,
                "most_active_times": [],
                "device_preferences": []
            }
        
        total_sessions = len(sessions)
        valid_durations = [s.session_duration for s in sessions if s.session_duration]
        avg_duration = sum(valid_durations) / len(valid_durations) if valid_durations else 0
        
        # Analyze time patterns
        time_counts = {}
        for session in sessions:
            if session.time_of_day:
                time_counts[session.time_of_day] = time_counts.get(session.time_of_day, 0) + 1
        
        most_active_times = sorted(time_counts.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        # Analyze device preferences
        device_counts = {}
        for session in sessions:
            if session.device_type:
                device_counts[session.device_type] = device_counts.get(session.device_type, 0) + 1
        
        device_preferences = sorted(device_counts.items(), 
                                  key=lambda x: x[1], reverse=True)
        
        return {
            "total_sessions": total_sessions,
            "average_session_duration": avg_duration,
            "most_active_times": most_active_times,
            "device_preferences": device_preferences
        }


class VideoInteractionRepository(BaseRepository):
    """Repository for video interaction operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, VideoInteractionLog)
    
    def log_interaction(self, user_id: int, interaction_data: Dict[str, Any]) -> VideoInteractionLog:
        """Log a video interaction"""
        return self.create(user_id=user_id, **interaction_data)
    
    def get_video_interaction_stats(self, video_id: int) -> Dict[str, Any]:
        """Get interaction statistics for a video"""
        interactions = self.db.query(VideoInteractionLog).filter(
            VideoInteractionLog.video_id == video_id
        ).all()
        
        if not interactions:
            return {
                "total_interactions": 0,
                "unique_users": 0,
                "interaction_types": {}
            }
        
        total_interactions = len(interactions)
        unique_users = len(set(i.user_id for i in interactions))
        
        # Count interaction types
        type_counts = {}
        for interaction in interactions:
            interaction_type = interaction.interaction_type
            type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1
        
        return {
            "total_interactions": total_interactions,
            "unique_users": unique_users,
            "interaction_types": type_counts
        }


class UserPreferencesRepository(BaseRepository):
    """Repository for user preferences operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserPreferences)
    
    def get_user_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Get user preferences"""
        return self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
    
    def update_user_preferences(self, user_id: int, 
                               preferences: Dict[str, Any]) -> UserPreferences:
        """Update or create user preferences"""
        existing = self.get_user_preferences(user_id)
        
        if existing:
            for key, value in preferences.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            return self.create(user_id=user_id, **preferences)
    
    def update_auto_learned_preferences(self, user_id: int, 
                                      auto_prefs: Dict[str, Any]) -> bool:
        """Update automatically learned preferences"""
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            preferences = self.create(user_id=user_id)
        
        # Update only auto-learned fields
        auto_fields = [
            'auto_preferred_categories', 'auto_preferred_duration',
            'auto_preferred_times', 'auto_engagement_patterns'
        ]
        
        for field in auto_fields:
            if field in auto_prefs:
                setattr(preferences, field, auto_prefs[field])
        
        preferences.updated_at = datetime.utcnow()
        self.db.commit()
        return True
