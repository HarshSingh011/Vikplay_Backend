"""
Video service layer for business logic and AI data processing
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from video.models.video_models import (
    Video, Category, UserVideoHistory, UserSearchHistory, 
    UserSession, UserPreferences, VideoInteractionLog
)


class VideoAnalyticsService:
    """Service for processing automatic data collection for AI recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_viewing_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        VIEWING HISTORY ANALYSIS
        Analyzes user's viewing patterns for AI recommendations
        """
        history = self.db.query(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).all()
        
        if not history:
            return {
                "total_videos_watched": 0,
                "favorite_categories": [],
                "avg_completion_rate": 0.0,
                "preferred_video_length": None,
                "viewing_times": [],
                "device_preferences": [],
                "engagement_level": "low"
            }
        
        # Calculate viewing patterns
        total_videos = len(history)
        avg_completion = sum(h.completion_percentage for h in history) / total_videos
        
        # Get favorite categories
        category_counts = self.db.query(
            Category.name, func.count(UserVideoHistory.id).label('count')
        ).join(Video).join(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).group_by(Category.name).order_by(desc('count')).all()
        
        favorite_categories = [cat.name for cat in category_counts[:5]]
        
        # Analyze device preferences
        device_counts = {}
        for h in history:
            if h.device_type:
                device_counts[h.device_type] = device_counts.get(h.device_type, 0) + 1
        
        preferred_devices = sorted(device_counts.keys(), 
                                 key=lambda x: device_counts[x], reverse=True)
        
        # Calculate engagement level
        liked_videos = len([h for h in history if h.liked is True])
        engagement_level = "high" if liked_videos / total_videos > 0.3 else "medium" if liked_videos / total_videos > 0.1 else "low"
        
        return {
            "total_videos_watched": total_videos,
            "favorite_categories": favorite_categories,
            "avg_completion_rate": avg_completion,
            "preferred_video_length": self._calculate_preferred_length(history),
            "viewing_times": self._get_viewing_time_patterns(user_id),
            "device_preferences": preferred_devices,
            "engagement_level": engagement_level,
            "recent_interests": self._get_recent_interests(user_id)
        }
    
    def get_user_search_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        SEARCH QUERY ANALYSIS
        Analyzes user's search behavior for AI recommendations
        """
        searches = self.db.query(UserSearchHistory).filter(
            UserSearchHistory.user_id == user_id
        ).order_by(desc(UserSearchHistory.searched_at)).all()
        
        if not searches:
            return {
                "total_searches": 0,
                "common_search_terms": [],
                "search_success_rate": 0.0,
                "preferred_search_times": [],
                "recent_searches": []
            }
        
        # Analyze search patterns
        total_searches = len(searches)
        successful_searches = len([s for s in searches if s.clicked_video_id is not None])
        success_rate = successful_searches / total_searches if total_searches > 0 else 0
        
        # Extract common search terms
        all_terms = []
        for search in searches:
            terms = search.search_query.lower().split()
            all_terms.extend(terms)
        
        # Count term frequency
        term_counts = {}
        for term in all_terms:
            if len(term) > 2:  # Filter out short words
                term_counts[term] = term_counts.get(term, 0) + 1
        
        common_terms = sorted(term_counts.keys(), 
                            key=lambda x: term_counts[x], reverse=True)[:10]
        
        # Get recent searches
        recent_searches = [s.search_query for s in searches[:10]]
        
        return {
            "total_searches": total_searches,
            "common_search_terms": common_terms,
            "search_success_rate": success_rate,
            "preferred_search_times": self._get_search_time_patterns(user_id),
            "recent_searches": recent_searches,
            "avg_click_position": self._calculate_avg_click_position(searches)
        }
    
    def get_user_session_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        SESSION PATTERN ANALYSIS
        Analyzes when and how users use the platform
        """
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "avg_session_duration": 0,
                "most_active_times": [],
                "preferred_devices": [],
                "weekend_vs_weekday": {"weekend": 0, "weekday": 0}
            }
        
        # Calculate session patterns
        total_sessions = len(sessions)
        valid_durations = [s.session_duration for s in sessions if s.session_duration]
        avg_duration = sum(valid_durations) / len(valid_durations) if valid_durations else 0
        
        # Time of day patterns
        time_counts = {}
        for session in sessions:
            if session.time_of_day:
                time_counts[session.time_of_day] = time_counts.get(session.time_of_day, 0) + 1
        
        most_active_times = sorted(time_counts.keys(), 
                                 key=lambda x: time_counts[x], reverse=True)
        
        # Device preferences
        device_counts = {}
        for session in sessions:
            if session.device_type:
                device_counts[session.device_type] = device_counts.get(session.device_type, 0) + 1
        
        preferred_devices = sorted(device_counts.keys(), 
                                 key=lambda x: device_counts[x], reverse=True)
        
        # Weekend vs weekday analysis
        weekend_sessions = len([s for s in sessions if s.is_weekend])
        weekday_sessions = total_sessions - weekend_sessions
        
        return {
            "total_sessions": total_sessions,
            "avg_session_duration": avg_duration,
            "most_active_times": most_active_times,
            "preferred_devices": preferred_devices,
            "weekend_vs_weekday": {
                "weekend": weekend_sessions,
                "weekday": weekday_sessions
            },
            "avg_videos_per_session": self._calculate_avg_videos_per_session(sessions)
        }
    
    def get_user_engagement_score(self, user_id: int) -> float:
        """
        ENGAGEMENT METRICS ANALYSIS
        Calculate comprehensive user engagement score (0-100)
        """
        # Get viewing history
        history = self.db.query(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).all()
        
        if not history:
            return 0.0
        
        # Calculate different engagement factors
        total_videos = len(history)
        
        # 1. Completion rate (0-30 points)
        avg_completion = sum(h.completion_percentage for h in history) / total_videos
        completion_score = min(avg_completion * 0.3, 30)
        
        # 2. Like rate (0-25 points)
        liked_videos = len([h for h in history if h.liked is True])
        like_rate = liked_videos / total_videos
        like_score = min(like_rate * 25, 25)
        
        # 3. Rating activity (0-20 points)
        rated_videos = len([h for h in history if h.rating is not None])
        rating_rate = rated_videos / total_videos
        rating_score = min(rating_rate * 20, 20)
        
        # 4. Session consistency (0-15 points)
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).count()
        consistency_score = min(sessions * 0.5, 15)
        
        # 5. Search engagement (0-10 points)
        searches = self.db.query(UserSearchHistory).filter(
            UserSearchHistory.user_id == user_id
        ).count()
        search_score = min(searches * 0.2, 10)
        
        total_score = completion_score + like_score + rating_score + consistency_score + search_score
        return min(total_score, 100.0)
    
    def get_content_preferences_from_behavior(self, user_id: int) -> Dict[str, Any]:
        """
        Automatically learned preferences from user behavior
        """
        # Get viewing history
        history = self.db.query(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).all()
        
        if not history:
            return {}
        
        # Analyze preferred video lengths
        video_durations = []
        for h in history:
            video = self.db.query(Video).filter(Video.id == h.video_id).first()
            if video and video.duration and h.completion_percentage > 70:  # Only well-watched videos
                video_durations.append(video.duration)
        
        preferred_duration = sum(video_durations) / len(video_durations) if video_durations else None
        
        # Analyze preferred content ratings
        content_ratings = []
        for h in history:
            video = self.db.query(Video).filter(Video.id == h.video_id).first()
            if video and video.content_rating and h.completion_percentage > 50:
                content_ratings.append(video.content_rating)
        
        # Count rating preferences
        rating_counts = {}
        for rating in content_ratings:
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        preferred_ratings = sorted(rating_counts.keys(), 
                                 key=lambda x: rating_counts[x], reverse=True)
        
        return {
            "auto_preferred_duration": preferred_duration,
            "auto_preferred_content_ratings": preferred_ratings[:3],
            "auto_preferred_categories": self._get_auto_preferred_categories(user_id),
            "auto_language_preferences": self._get_auto_language_preferences(user_id)
        }
    
    # Helper methods
    def _calculate_preferred_length(self, history: List) -> Optional[int]:
        """Calculate user's preferred video length based on completion rates"""
        length_completion = {}
        
        for h in history:
            video = self.db.query(Video).filter(Video.id == h.video_id).first()
            if video and video.duration:
                duration_range = self._get_duration_range(video.duration)
                if duration_range not in length_completion:
                    length_completion[duration_range] = []
                length_completion[duration_range].append(h.completion_percentage)
        
        # Find duration range with highest average completion
        best_range = None
        best_completion = 0
        
        for duration_range, completions in length_completion.items():
            avg_completion = sum(completions) / len(completions)
            if avg_completion > best_completion:
                best_completion = avg_completion
                best_range = duration_range
        
        return best_range
    
    def _get_duration_range(self, duration: int) -> str:
        """Categorize video duration into ranges"""
        if duration < 300:  # 5 minutes
            return "short"
        elif duration < 1200:  # 20 minutes
            return "medium"
        else:
            return "long"
    
    def _get_viewing_time_patterns(self, user_id: int) -> List[str]:
        """Get user's preferred viewing times"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).all()
        
        time_counts = {}
        for session in sessions:
            if session.time_of_day:
                time_counts[session.time_of_day] = time_counts.get(session.time_of_day, 0) + 1
        
        return sorted(time_counts.keys(), key=lambda x: time_counts[x], reverse=True)
    
    def _get_recent_interests(self, user_id: int, days: int = 30) -> List[str]:
        """Get user's recent category interests"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_categories = self.db.query(Category.name).join(Video).join(UserVideoHistory).filter(
            and_(
                UserVideoHistory.user_id == user_id,
                UserVideoHistory.watched_at >= cutoff_date
            )
        ).distinct().all()
        
        return [cat.name for cat in recent_categories]
    
    def _get_search_time_patterns(self, user_id: int) -> List[str]:
        """Analyze when user typically searches"""
        searches = self.db.query(UserSearchHistory).filter(
            UserSearchHistory.user_id == user_id
        ).all()
        
        time_patterns = {}
        for search in searches:
            hour = search.searched_at.hour
            if 6 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 22:
                time_of_day = "evening"
            else:
                time_of_day = "night"
            
            time_patterns[time_of_day] = time_patterns.get(time_of_day, 0) + 1
        
        return sorted(time_patterns.keys(), key=lambda x: time_patterns[x], reverse=True)
    
    def _calculate_avg_click_position(self, searches: List) -> float:
        """Calculate average position of clicked search results"""
        click_positions = [s.click_position for s in searches if s.click_position is not None]
        return sum(click_positions) / len(click_positions) if click_positions else 0.0
    
    def _calculate_avg_videos_per_session(self, sessions: List) -> float:
        """Calculate average videos watched per session"""
        video_counts = [s.videos_watched for s in sessions if s.videos_watched > 0]
        return sum(video_counts) / len(video_counts) if video_counts else 0.0
    
    def _get_auto_preferred_categories(self, user_id: int) -> List[str]:
        """Get automatically learned category preferences"""
        # Categories with high completion rates
        category_completion = self.db.query(
            Category.name, 
            func.avg(UserVideoHistory.completion_percentage).label('avg_completion')
        ).join(Video).join(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).group_by(Category.name).having(
            func.avg(UserVideoHistory.completion_percentage) > 70
        ).order_by(desc('avg_completion')).all()
        
        return [cat.name for cat in category_completion[:5]]
    
    def _get_auto_language_preferences(self, user_id: int) -> List[str]:
        """Get automatically learned language preferences"""
        language_counts = self.db.query(
            Video.language, func.count(UserVideoHistory.id).label('count')
        ).join(UserVideoHistory).filter(
            UserVideoHistory.user_id == user_id
        ).group_by(Video.language).order_by(desc('count')).all()
        
        return [lang.language for lang in language_counts[:3]]
