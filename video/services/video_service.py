"""
Video Service Layer - Business Logic Layer
Implements clean architecture with dependency injection
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
import logging

from video.repositories.video_repository import (
    VideoRepository, CategoryRepository, UserVideoHistoryRepository,
    UserSearchHistoryRepository, UserSessionRepository, VideoInteractionRepository
)
from video.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse, CategoryCreate,
    WatchProgressUpdateEnhanced, VideoEngagement, VideoInteraction,
    SearchQueryLog, UserAnalytics, VideoAnalytics
)

logger = logging.getLogger(__name__)


# Service Interfaces (Clean Architecture)
class IVideoService(ABC):
    """Interface for Video Service"""
    
    @abstractmethod
    async def create_video(self, video_data: VideoCreate) -> VideoResponse: pass
    
    @abstractmethod
    async def get_video(self, video_id: int) -> Optional[VideoResponse]: pass
    
    @abstractmethod
    async def search_videos(self, query: str, filters: Optional[Dict] = None) -> List[VideoResponse]: pass


class IAnalyticsService(ABC):
    """Interface for Analytics Service"""
    
    @abstractmethod
    async def track_viewing_progress(self, user_id: int, progress_data: WatchProgressUpdateEnhanced) -> bool: pass
    
    @abstractmethod
    async def get_user_analytics(self, user_id: int) -> UserAnalytics: pass


# Service Implementations
class VideoService(IVideoService):
    """Video business logic service with clean architecture"""
    
    def __init__(self, video_repo: VideoRepository, category_repo: CategoryRepository):
        self.video_repo = video_repo
        self.category_repo = category_repo
    
    async def create_video(self, video_data: VideoCreate) -> VideoResponse:
        """Create a new video with validation"""
        try:
            # Validate category exists if provided
            if video_data.category_id:
                category = self.category_repo.get_by_id(video_data.category_id)
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Category not found"
                    )
            
            # Create video
            video_dict = video_data.model_dump()
            video = self.video_repo.create(video_dict)
            
            logger.info(f"Video created successfully: {video.id}")
            return VideoResponse.model_validate(video)
            
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create video"
            )
    
    async def get_video(self, video_id: int) -> Optional[VideoResponse]:
        """Get video by ID with error handling"""
        try:
            video = self.video_repo.get_by_id(video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            return VideoResponse.model_validate(video)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting video {video_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve video"
            )
    
    async def get_videos(self, skip: int = 0, limit: int = 20) -> List[VideoResponse]:
        """Get list of videos with pagination"""
        try:
            videos = self.video_repo.get_all(skip=skip, limit=limit)
            return [VideoResponse.model_validate(video) for video in videos]
            
        except Exception as e:
            logger.error(f"Error getting videos: {str(e)}")
            # Return empty list instead of raising exception if no videos found
            return []
    
    async def get_videos_by_category(self, category_id: int, skip: int = 0, limit: int = 20) -> List[VideoResponse]:
        """Get videos by category with pagination"""
        try:
            # Check if category exists
            category = self.category_repo.get_by_id(category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            videos = self.video_repo.get_by_category(category_id, skip=skip, limit=limit)
            return [VideoResponse.model_validate(video) for video in videos]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting videos by category {category_id}: {str(e)}")
            return []
    
    async def update_video(self, video_id: int, update_data: VideoUpdate) -> Optional[VideoResponse]:
        """Update video with validation"""
        try:
            # Check if video exists
            existing_video = self.video_repo.get_by_id(video_id)
            if not existing_video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            # Validate category if being updated
            if update_data.category_id:
                category = self.category_repo.get_by_id(update_data.category_id)
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Category not found"
                    )
            
            # Update video
            update_dict = update_data.model_dump(exclude_unset=True)
            updated_video = self.video_repo.update(video_id, update_dict)
            
            logger.info(f"Video updated successfully: {video_id}")
            return VideoResponse.model_validate(updated_video)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating video {video_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update video"
            )
    
    async def delete_video(self, video_id: int) -> bool:
        """Delete video with validation"""
        try:
            success = self.video_repo.delete(video_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            logger.info(f"Video deleted successfully: {video_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete video"
            )
    
    async def search_videos(self, query: str, filters: Optional[Dict] = None, 
                           skip: int = 0, limit: int = 20) -> List[VideoResponse]:
        """Search videos with filters"""
        try:
            if not query.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search query cannot be empty"
                )
            
            videos = self.video_repo.search_videos(query, filters, skip, limit)
            return [VideoResponse.model_validate(video) for video in videos]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search videos"
            )
    
    async def get_popular_videos(self, limit: int = 20) -> List[VideoResponse]:
        """Get popular videos"""
        try:
            videos = self.video_repo.get_popular_videos(limit)
            return [VideoResponse.model_validate(video) for video in videos]
            
        except Exception as e:
            logger.error(f"Error getting popular videos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get popular videos"
            )
    
    async def get_trending_videos(self, days: int = 7, limit: int = 20) -> List[VideoResponse]:
        """Get trending videos"""
        try:
            videos = self.video_repo.get_trending_videos(days, limit)
            return [VideoResponse.model_validate(video) for video in videos]
            
        except Exception as e:
            logger.error(f"Error getting trending videos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get trending videos"
            )


class AnalyticsService(IAnalyticsService):
    """Analytics business logic service"""
    
    def __init__(self, 
                 video_repo: VideoRepository,
                 history_repo: UserVideoHistoryRepository,
                 search_repo: UserSearchHistoryRepository,
                 session_repo: UserSessionRepository,
                 interaction_repo: VideoInteractionRepository):
        self.video_repo = video_repo
        self.history_repo = history_repo
        self.search_repo = search_repo
        self.session_repo = session_repo
        self.interaction_repo = interaction_repo
    
    async def track_viewing_progress(self, user_id: int, 
                                   progress_data: WatchProgressUpdateEnhanced) -> Dict[str, str]:
        """Track user viewing progress with business logic"""
        try:
            # Validate video exists
            video = self.video_repo.get_by_id(progress_data.video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            # Validate progress data
            if progress_data.completion_percentage < 0 or progress_data.completion_percentage > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Completion percentage must be between 0 and 100"
                )
            
            if progress_data.watch_duration < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Watch duration cannot be negative"
                )
            
            # Update viewing progress
            self.history_repo.update_watch_progress(
                user_id=user_id,
                video_id=progress_data.video_id,
                session_id=progress_data.session_id or f"session_{user_id}_{datetime.now().timestamp()}",
                watch_duration=progress_data.watch_duration,
                completion_percentage=progress_data.completion_percentage,
                device_type=progress_data.device_type
            )
            
            # Update video engagement metrics (async task)
            self.video_repo.update_engagement_metrics(progress_data.video_id)
            
            logger.info(f"Viewing progress tracked for user {user_id}, video {progress_data.video_id}")
            return {"status": "success", "message": "Viewing progress tracked"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error tracking viewing progress: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track viewing progress"
            )
    
    async def track_engagement(self, user_id: int, engagement_data: VideoEngagement) -> Dict[str, str]:
        """Track user engagement with validation"""
        try:
            # Validate video exists
            video = self.video_repo.get_by_id(engagement_data.video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            # Validate rating range
            if engagement_data.rating is not None and (engagement_data.rating < 1 or engagement_data.rating > 5):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rating must be between 1 and 5"
                )
            
            # Update engagement
            result = self.history_repo.update_engagement(
                user_id=user_id,
                video_id=engagement_data.video_id,
                rating=engagement_data.rating,
                liked=engagement_data.liked,
                shared=engagement_data.shared,
                bookmarked=engagement_data.bookmarked
            )
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No viewing history found for this video"
                )
            
            # Update video metrics
            self.video_repo.update_engagement_metrics(engagement_data.video_id)
            
            logger.info(f"Engagement tracked for user {user_id}, video {engagement_data.video_id}")
            return {"status": "success", "message": "Engagement tracked"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error tracking engagement: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track engagement"
            )
    
    async def track_interaction(self, user_id: int, interaction_data: VideoInteraction) -> Dict[str, str]:
        """Track detailed video interactions"""
        try:
            # Validate video exists
            video = self.video_repo.get_by_id(interaction_data.video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            # Log interaction
            self.interaction_repo.log_interaction(
                user_id=user_id,
                video_id=interaction_data.video_id,
                interaction_type=interaction_data.interaction_type,
                interaction_value=interaction_data.interaction_value,
                video_timestamp=interaction_data.video_timestamp,
                session_id=interaction_data.session_id,
                device_type=interaction_data.device_type
            )
            
            logger.info(f"Interaction tracked: {interaction_data.interaction_type} for user {user_id}")
            return {"status": "success", "message": "Interaction tracked"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track interaction"
            )
    
    async def get_user_analytics(self, user_id: int) -> UserAnalytics:
        """Get comprehensive user analytics"""
        try:
            # Get basic analytics from repository
            basic_analytics = self.history_repo.get_user_analytics(user_id)
            
            # Get search patterns
            search_patterns = self.search_repo.get_user_search_patterns(user_id)
            
            # Combine data for comprehensive analytics
            return UserAnalytics(
                total_videos_watched=basic_analytics["total_videos_watched"],
                total_watch_time=basic_analytics["total_watch_time"],
                average_completion_rate=basic_analytics["average_completion_rate"],
                favorite_categories=[],  # Will be populated by repository
                most_active_times=[],    # Will be populated by repository
                preferred_video_length=0,  # Will be calculated
                engagement_score=0.0,    # Will be calculated
                recent_interests=[]      # Will be populated by repository
            )
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user analytics"
            )


class SearchService:
    """Search service with enhanced tracking"""
    
    def __init__(self, video_repo: VideoRepository, search_repo: UserSearchHistoryRepository):
        self.video_repo = video_repo
        self.search_repo = search_repo
    
    async def search_with_tracking(self, user_id: int, search_data: SearchQueryLog) -> Dict[str, Any]:
        """Enhanced search with automatic tracking"""
        try:
            # Validate search query
            if not search_data.search_query.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search query cannot be empty"
                )
            
            # Perform search
            results = self.video_repo.search_videos(
                query=search_data.search_query,
                filters=search_data.search_filters,
                limit=20
            )
            
            # Log search automatically
            search_log = self.search_repo.create_search_log(
                user_id=user_id,
                search_query=search_data.search_query,
                results_count=len(results),
                search_filters=search_data.search_filters,
                device_type=search_data.device_type
            )
            
            # Convert to response format
            video_responses = [VideoResponse.model_validate(video) for video in results]
            
            logger.info(f"Search performed by user {user_id}: '{search_data.search_query}'")
            
            return {
                "search_id": search_log.id,
                "results": video_responses,
                "total_results": len(results),
                "query": search_data.search_query
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to perform search"
            )
    
    async def track_search_click(self, user_id: int, search_id: int, 
                               clicked_video_id: int, click_position: int,
                               time_to_click: Optional[float] = None) -> Dict[str, str]:
        """Track search result clicks"""
        try:
            # Validate video exists
            video = self.video_repo.get_by_id(clicked_video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            # Update search log
            success = self.search_repo.update_search_click(
                search_id=search_id,
                clicked_video_id=clicked_video_id,
                click_position=click_position,
                time_to_click=time_to_click
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Search record not found"
                )
            
            logger.info(f"Search click tracked: position {click_position} for user {user_id}")
            return {"status": "success", "message": "Search click tracked"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error tracking search click: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track search click"
            )


class SessionService:
    """Session management service"""
    
    def __init__(self, session_repo: UserSessionRepository):
        self.session_repo = session_repo
    
    async def start_session(self, user_id: int, session_id: str, 
                          device_info: Dict[str, Any]) -> Dict[str, str]:
        """Start a new user session"""
        try:
            session = self.session_repo.create_session(
                user_id=user_id,
                session_id=session_id,
                device_info=device_info
            )
            
            logger.info(f"Session started for user {user_id}: {session_id}")
            return {"status": "success", "session_id": session.session_id}
            
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start session"
            )
    
    async def update_session_activity(self, user_id: int, session_id: str,
                                    activity_data: Dict[str, int]) -> Dict[str, str]:
        """Update session activity"""
        try:
            session = self.session_repo.update_session_activity(
                session_id=session_id,
                user_id=user_id,
                **activity_data
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            return {"status": "success", "message": "Session activity updated"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update session activity"
            )
    
    async def end_session(self, user_id: int, session_id: str, 
                         session_duration: int) -> Dict[str, str]:
        """End a user session"""
        try:
            session = self.session_repo.end_session(
                session_id=session_id,
                user_id=user_id,
                session_duration=session_duration
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            logger.info(f"Session ended for user {user_id}: {session_id}")
            return {"status": "success", "message": "Session ended"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to end session"
            )
