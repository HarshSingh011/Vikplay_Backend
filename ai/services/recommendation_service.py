"""
AI Recommendation Service - Intelligent video recommendations using Ollama + ChromaDB
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import json
import random

from ai.models.video_embedding import VideoEmbeddingModel
from video.repositories.video_repository import VideoRepository, UserHistoryRepository, UserPreferencesRepository
from models.models import Video, UserVideoHistory, UserPreferences

logger = logging.getLogger(__name__)

class VideoRecommendationService:
    """AI-powered video recommendation service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.history_repo = UserHistoryRepository(db)
        self.preferences_repo = UserPreferencesRepository(db)
        self.embedding_model = VideoEmbeddingModel()
    
    def get_recommendations(self, user_id: str, limit: int = 10, 
                          exclude_watched: bool = True) -> Dict[str, Any]:
        """Get personalized video recommendations for a user"""
        try:
            # Get user's watch history
            user_history = self.history_repo.get_user_history(user_id, limit=100)
            user_preferences = self.preferences_repo.get_user_preferences(user_id)
            
            # Get videos to exclude
            exclude_ids = []
            if exclude_watched:
                exclude_ids = [h.video_id for h in user_history]
            
            # Generate recommendations using multiple strategies
            recommendations = []
            
            # Strategy 1: Content-based filtering (similar to watched videos)
            content_based = self._get_content_based_recommendations(
                user_history, limit=limit//2, exclude_ids=exclude_ids
            )
            recommendations.extend(content_based)
            
            # Strategy 2: Collaborative filtering (popular among similar users)
            collaborative = self._get_collaborative_recommendations(
                user_id, user_history, limit=limit//3, exclude_ids=exclude_ids
            )
            recommendations.extend(collaborative)
            
            # Strategy 3: Category-based recommendations
            category_based = self._get_category_based_recommendations(
                user_history, user_preferences, limit=limit//4, exclude_ids=exclude_ids
            )
            recommendations.extend(category_based)
            
            # Strategy 4: Trending/Popular videos
            if len(recommendations) < limit:
                trending = self._get_trending_recommendations(
                    limit=limit-len(recommendations), exclude_ids=exclude_ids
                )
                recommendations.extend(trending)
            
            # Remove duplicates and sort by score
            unique_recommendations = {}
            for video_id, score, reason in recommendations:
                if video_id not in unique_recommendations:
                    unique_recommendations[video_id] = (score, reason)
                else:
                    # Keep the higher score
                    if score > unique_recommendations[video_id][0]:
                        unique_recommendations[video_id] = (score, reason)
            
            # Sort by score and get top recommendations
            sorted_recommendations = sorted(
                unique_recommendations.items(), 
                key=lambda x: x[1][0], 
                reverse=True
            )[:limit]
            
            # Get video details
            recommended_videos = []
            for video_id, (score, reason) in sorted_recommendations:
                video = self.video_repo.get_video_by_id(video_id)
                if video:
                    recommended_videos.append({
                        "video": video,
                        "score": score,
                        "reason": reason
                    })
            
            return {
                "recommendations": recommended_videos,
                "total_count": len(recommended_videos),
                "strategies_used": ["content_based", "collaborative", "category_based", "trending"],
                "user_history_count": len(user_history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get recommendations for user {user_id}: {str(e)}")
            # Fallback to popular videos
            return self._get_fallback_recommendations(limit, exclude_ids)
    
    def _get_content_based_recommendations(self, user_history: List[UserVideoHistory], 
                                         limit: int, exclude_ids: List[int]) -> List[Tuple[int, float, str]]:
        """Get recommendations based on content similarity"""
        if not user_history:
            return []
        
        try:
            # Get recently watched and highly rated videos
            recent_videos = [h.video_id for h in user_history[:10]]  # Last 10 videos
            highly_rated = [h.video_id for h in user_history if h.rating and h.rating >= 4]
            liked_videos = [h.video_id for h in user_history if h.liked is True]
            
            # Combine and prioritize
            reference_videos = list(set(highly_rated + liked_videos + recent_videos))[:5]
            
            if not reference_videos:
                return []
            
            # Find similar videos using embeddings
            similar_videos = self.embedding_model.find_similar_videos(
                reference_video_ids=reference_videos,
                exclude_ids=exclude_ids + reference_videos,
                limit=limit
            )
            
            recommendations = []
            for video_id, similarity in similar_videos:
                score = similarity * 0.8  # Content-based gets 80% weight
                reason = "Similar to videos you enjoyed"
                recommendations.append((video_id, score, reason))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Content-based recommendations failed: {str(e)}")
            return []
    
    def _get_collaborative_recommendations(self, user_id: str, user_history: List[UserVideoHistory], 
                                         limit: int, exclude_ids: List[int]) -> List[Tuple[int, float, str]]:
        """Get recommendations based on similar users' preferences"""
        try:
            if not user_history:
                return []
            
            # Get user's watched video IDs
            user_watched = set([h.video_id for h in user_history])
            
            # Find users with similar watch patterns
            similar_users = self._find_similar_users(user_id, user_watched, limit=20)
            
            recommendations = []
            for similar_user_id, similarity in similar_users:
                # Get videos watched by similar user but not by current user
                similar_user_history = self.history_repo.get_user_history(similar_user_id, limit=50)
                
                for history in similar_user_history:
                    if (history.video_id not in user_watched and 
                        history.video_id not in exclude_ids and
                        history.completion_percentage > 50):  # Only recommend if they watched most of it
                        
                        # Score based on similarity and user's rating
                        base_score = similarity * 0.6
                        if history.rating:
                            base_score *= (history.rating / 5.0)
                        if history.liked:
                            base_score *= 1.2
                        
                        recommendations.append((
                            history.video_id, 
                            base_score, 
                            f"Liked by users with similar taste"
                        ))
            
            # Sort and return top recommendations
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Collaborative recommendations failed: {str(e)}")
            return []
    
    def _find_similar_users(self, user_id: str, user_watched: set, limit: int = 20) -> List[Tuple[str, float]]:
        """Find users with similar viewing patterns"""
        try:
            # Get all users who watched similar videos
            similar_users = {}
            
            for video_id in list(user_watched)[:20]:  # Limit to recent videos for performance
                # Get other users who watched this video
                other_viewers = (self.db.query(UserVideoHistory.user_id)
                               .filter(UserVideoHistory.video_id == video_id)
                               .filter(UserVideoHistory.user_id != user_id)
                               .filter(UserVideoHistory.completion_percentage > 30)
                               .all())
                
                for (other_user_id,) in other_viewers:
                    if other_user_id not in similar_users:
                        similar_users[other_user_id] = 0
                    similar_users[other_user_id] += 1
            
            # Calculate similarity scores
            similarity_scores = []
            for other_user_id, common_videos in similar_users.items():
                if common_videos >= 2:  # At least 2 videos in common
                    # Get other user's total watched videos
                    other_user_history = self.history_repo.get_user_history(other_user_id, limit=100)
                    other_watched = set([h.video_id for h in other_user_history])
                    
                    # Calculate Jaccard similarity
                    intersection = len(user_watched & other_watched)
                    union = len(user_watched | other_watched)
                    
                    if union > 0:
                        similarity = intersection / union
                        similarity_scores.append((other_user_id, similarity))
            
            # Sort by similarity
            similarity_scores.sort(key=lambda x: x[1], reverse=True)
            return similarity_scores[:limit]
            
        except Exception as e:
            logger.error(f"Finding similar users failed: {str(e)}")
            return []
    
    def _get_category_based_recommendations(self, user_history: List[UserVideoHistory], 
                                          user_preferences: Optional[UserPreferences],
                                          limit: int, exclude_ids: List[int]) -> List[Tuple[int, float, str]]:
        """Get recommendations based on user's favorite categories"""
        try:
            # Get user's favorite categories from history
            favorite_categories = self.history_repo.get_user_favorite_categories(
                user_history[0].user_id if user_history else "", limit=5
            )
            
            # Add preferred categories from user preferences
            if user_preferences and user_preferences.preferred_categories:
                try:
                    preferred_cats = json.loads(user_preferences.preferred_categories)
                    for cat_id in preferred_cats:
                        favorite_categories.append({
                            "category_id": cat_id, 
                            "category_name": "", 
                            "watch_count": 10  # Give preference weight
                        })
                except:
                    pass
            
            if not favorite_categories:
                return []
            
            recommendations = []
            for cat_info in favorite_categories[:3]:  # Top 3 categories
                category_id = cat_info["category_id"]
                watch_count = cat_info["watch_count"]
                
                # Get popular videos from this category
                category_videos = self.video_repo.get_videos_by_category(category_id, limit=limit)
                
                for video in category_videos:
                    if video.id not in exclude_ids:
                        # Score based on category preference and video popularity
                        score = (watch_count / 10.0) * 0.5 + (video.view_count / 1000.0) * 0.3
                        score = min(score, 1.0)  # Cap at 1.0
                        
                        recommendations.append((
                            video.id, 
                            score, 
                            f"From your favorite category: {cat_info['category_name']}"
                        ))
            
            # Sort and return top recommendations
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Category-based recommendations failed: {str(e)}")
            return []
    
    def _get_trending_recommendations(self, limit: int, exclude_ids: List[int]) -> List[Tuple[int, float, str]]:
        """Get trending/popular videos"""
        try:
            # Get popular videos from last 30 days
            popular_videos = self.video_repo.get_popular_videos(limit=limit*2)
            
            recommendations = []
            for video in popular_videos:
                if video.id not in exclude_ids:
                    # Score based on view count and recency
                    days_old = (datetime.utcnow() - video.created_at).days
                    recency_factor = max(0.1, 1.0 - (days_old / 30.0))  # Newer videos get higher score
                    score = (video.view_count / 1000.0) * recency_factor * 0.4
                    score = min(score, 1.0)
                    
                    recommendations.append((
                        video.id, 
                        score, 
                        "Trending now"
                    ))
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Trending recommendations failed: {str(e)}")
            return []
    
    def _get_fallback_recommendations(self, limit: int, exclude_ids: List[int]) -> Dict[str, Any]:
        """Fallback recommendations when AI fails"""
        try:
            popular_videos = self.video_repo.get_popular_videos(limit=limit*2)
            
            recommendations = []
            for video in popular_videos:
                if video.id not in exclude_ids:
                    recommendations.append({
                        "video": video,
                        "score": 0.5,
                        "reason": "Popular video"
                    })
            
            return {
                "recommendations": recommendations[:limit],
                "total_count": len(recommendations[:limit]),
                "strategies_used": ["fallback_popular"],
                "user_history_count": 0
            }
            
        except Exception as e:
            logger.error(f"Fallback recommendations failed: {str(e)}")
            return {
                "recommendations": [],
                "total_count": 0,
                "strategies_used": ["none"],
                "user_history_count": 0
            }
    
    def get_recommendations_for_current_video(self, user_id: str, current_video_id: int, 
                                            limit: int = 5) -> Dict[str, Any]:
        """Get recommendations based on the currently watching video"""
        try:
            # Get similar videos to current video
            similar_videos = self.embedding_model.find_similar_videos(
                reference_video_ids=[current_video_id],
                exclude_ids=[current_video_id],
                limit=limit
            )
            
            recommendations = []
            for video_id, similarity in similar_videos:
                video = self.video_repo.get_video_by_id(video_id)
                if video:
                    recommendations.append({
                        "video": video,
                        "score": similarity,
                        "reason": "Similar to current video"
                    })
            
            return {
                "recommendations": recommendations,
                "total_count": len(recommendations),
                "strategies_used": ["current_video_similarity"],
                "current_video_id": current_video_id
            }
            
        except Exception as e:
            logger.error(f"Current video recommendations failed: {str(e)}")
            return self._get_fallback_recommendations(limit, [current_video_id])
    
    def search_recommendations(self, query: str, limit: int = 10, 
                             exclude_ids: List[int] = None) -> Dict[str, Any]:
        """Search-based recommendations using natural language"""
        try:
            exclude_ids = exclude_ids or []
            
            # Use embedding model to search
            search_results = self.embedding_model.search_videos_by_query(
                query=query,
                limit=limit,
                exclude_ids=exclude_ids
            )
            
            recommendations = []
            for video_id, similarity in search_results:
                video = self.video_repo.get_video_by_id(video_id)
                if video:
                    recommendations.append({
                        "video": video,
                        "score": similarity,
                        "reason": f"Matches your search: '{query}'"
                    })
            
            return {
                "recommendations": recommendations,
                "total_count": len(recommendations),
                "strategies_used": ["semantic_search"],
                "search_query": query
            }
            
        except Exception as e:
            logger.error(f"Search recommendations failed: {str(e)}")
            return self._get_fallback_recommendations(limit, exclude_ids)
    
    def initialize_embeddings_for_video(self, video: Video):
        """Initialize embeddings for a new video"""
        try:
            video_data = {
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "category": video.category.name if video.category else "",
                "category_id": video.category_id,
                "tags": video.tags,
                "view_count": video.view_count,
                "created_at": video.created_at,
                "duration": video.duration
            }
            
            self.embedding_model.add_video_embedding(video.id, video_data)
            logger.info(f"Initialized embeddings for video {video.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embeddings for video {video.id}: {str(e)}")
    
    def rebuild_all_embeddings(self):
        """Rebuild embeddings for all videos"""
        try:
            # Get all videos
            videos = self.video_repo.get_videos(limit=10000)  # Adjust limit as needed
            
            videos_data = []
            for video in videos:
                video_data = {
                    "id": video.id,
                    "title": video.title,
                    "description": video.description,
                    "category": video.category.name if video.category else "",
                    "category_id": video.category_id,
                    "tags": video.tags,
                    "view_count": video.view_count,
                    "created_at": video.created_at,
                    "duration": video.duration
                }
                videos_data.append(video_data)
            
            self.embedding_model.rebuild_embeddings(videos_data)
            logger.info(f"Rebuilt embeddings for {len(videos_data)} videos")
            
        except Exception as e:
            logger.error(f"Failed to rebuild embeddings: {str(e)}")
            raise
    
    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get statistics about the recommendation system"""
        try:
            embedding_stats = self.embedding_model.get_collection_stats()
            
            # Get user history stats
            total_users = self.db.query(UserVideoHistory.user_id).distinct().count()
            total_interactions = self.db.query(UserVideoHistory).count()
            
            return {
                "embedding_stats": embedding_stats,
                "total_users_with_history": total_users,
                "total_interactions": total_interactions,
                "recommendation_engine": "Ollama + ChromaDB"
            }
            
        except Exception as e:
            logger.error(f"Failed to get recommendation stats: {str(e)}")
            return {"error": str(e)}
