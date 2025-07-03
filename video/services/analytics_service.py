"""
Analytics Service - AI Data Collection Business Logic
Handles viewing progress, engagement tracking, and analytics
"""
from typing import Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
import logging

from video.services.interfaces import IAnalyticsService
from video.repositories.video_repository import (
    VideoRepository, UserVideoHistoryRepository, VideoInteractionRepository
)
from video.schemas.video_schemas import (
    WatchProgressUpdateEnhanced, VideoEngagement, VideoInteraction, UserAnalytics
)

logger = logging.getLogger(__name__)


class AnalyticsService(IAnalyticsService):
    """Analytics business logic service for AI data collection"""
    
    def __init__(self, 
                 video_repo: VideoRepository,
                 history_repo: UserVideoHistoryRepository,
                 interaction_repo: VideoInteractionRepository):
        self.video_repo = video_repo
        self.history_repo = history_repo
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
            
            # Combine data for comprehensive analytics
            return UserAnalytics(
                total_videos_watched=basic_analytics.get("total_videos_watched", 0),
                total_watch_time=basic_analytics.get("total_watch_time", 0),
                average_completion_rate=basic_analytics.get("average_completion_rate", 0.0),
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
