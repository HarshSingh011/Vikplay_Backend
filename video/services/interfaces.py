"""
Service Interfaces - Clean Architecture Contracts
Define abstractions for business logic services
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from video.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse,
    WatchProgressUpdateEnhanced, VideoEngagement, VideoInteraction,
    SearchQueryLog, UserAnalytics
)


class IVideoService(ABC):
    """Interface for Video Service"""
    
    @abstractmethod
    async def create_video(self, video_data: VideoCreate) -> VideoResponse:
        """Create a new video"""
        pass
    
    @abstractmethod
    async def get_video(self, video_id: int) -> Optional[VideoResponse]:
        """Get video by ID"""
        pass
    
    @abstractmethod
    async def get_videos(self, skip: int = 0, limit: int = 20) -> List[VideoResponse]:
        """Get list of videos with pagination"""
        pass
    
    @abstractmethod
    async def get_videos_by_category(self, category_id: int, skip: int = 0, limit: int = 20) -> List[VideoResponse]:
        """Get videos by category"""
        pass
    
    @abstractmethod
    async def update_video(self, video_id: int, update_data: VideoUpdate) -> Optional[VideoResponse]:
        """Update video"""
        pass
    
    @abstractmethod
    async def delete_video(self, video_id: int) -> bool:
        """Delete video"""
        pass
    
    @abstractmethod
    async def search_videos(self, query: str, filters: Optional[Dict] = None, skip: int = 0, limit: int = 20) -> List[VideoResponse]:
        """Search videos with filters"""
        pass
    
    @abstractmethod
    async def get_popular_videos(self, limit: int = 20) -> List[VideoResponse]:
        """Get popular videos"""
        pass
    
    @abstractmethod
    async def get_trending_videos(self, days: int = 7, limit: int = 20) -> List[VideoResponse]:
        """Get trending videos"""
        pass


class IAnalyticsService(ABC):
    """Interface for Analytics Service"""
    
    @abstractmethod
    async def track_viewing_progress(self, user_id: int, progress_data: WatchProgressUpdateEnhanced) -> Dict[str, str]:
        """Track user viewing progress"""
        pass
    
    @abstractmethod
    async def track_engagement(self, user_id: int, engagement_data: VideoEngagement) -> Dict[str, str]:
        """Track user engagement"""
        pass
    
    @abstractmethod
    async def track_interaction(self, user_id: int, interaction_data: VideoInteraction) -> Dict[str, str]:
        """Track video interactions"""
        pass
    
    @abstractmethod
    async def get_user_analytics(self, user_id: int) -> UserAnalytics:
        """Get user analytics"""
        pass


class ISearchService(ABC):
    """Interface for Search Service"""
    
    @abstractmethod
    async def search_with_tracking(self, user_id: int, search_data: SearchQueryLog) -> Dict[str, Any]:
        """Enhanced search with tracking"""
        pass
    
    @abstractmethod
    async def track_search_click(self, user_id: int, search_id: int, clicked_video_id: int, 
                               click_position: int, time_to_click: Optional[float] = None) -> Dict[str, str]:
        """Track search result clicks"""
        pass


class ISessionService(ABC):
    """Interface for Session Service"""
    
    @abstractmethod
    async def start_session(self, user_id: int, session_id: str, device_info: Dict[str, Any]) -> Dict[str, str]:
        """Start user session"""
        pass
    
    @abstractmethod
    async def update_session_activity(self, user_id: int, session_id: str, activity_data: Dict[str, int]) -> Dict[str, str]:
        """Update session activity"""
        pass
    
    @abstractmethod
    async def end_session(self, user_id: int, session_id: str, session_duration: int) -> Dict[str, str]:
        """End user session"""
        pass


class ICategoryService(ABC):
    """Interface for Category Service"""
    
    @abstractmethod
    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new category"""
        pass
    
    @abstractmethod
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        pass
    
    @abstractmethod
    async def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID"""
        pass
