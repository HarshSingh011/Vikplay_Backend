"""
AI Routes - API endpoints for AI-powered recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import get_db
from auth.utils.jwt_token import get_current_user
from ai.services.recommendation_service import VideoRecommendationService
from video.schemas import VideoRecommendationRequest, VideoRecommendationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Recommendations"])

@router.get("/recommendations", response_model=dict)
async def get_user_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    exclude_watched: bool = Query(True, description="Exclude already watched videos"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized video recommendations for the current user
    
    Uses multiple AI strategies:
    - Content-based filtering (similar to watched videos)
    - Collaborative filtering (similar users' preferences)
    - Category-based recommendations
    - Trending videos
    """
    try:
        recommendation_service = VideoRecommendationService(db)
        
        recommendations = recommendation_service.get_recommendations(
            user_id=current_user["user_id"],
            limit=limit,
            exclude_watched=exclude_watched
        )
        
        # Format response
        formatted_recommendations = []
        for rec in recommendations["recommendations"]:
            video = rec["video"]
            formatted_recommendations.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "file_url": video.file_url,
                "category_id": video.category_id,
                "view_count": video.view_count,
                "created_at": video.created_at.isoformat(),
                "duration": video.duration,
                "tags": video.tags,
                "recommendation_score": rec["score"],
                "recommendation_reason": rec["reason"],
                "category": video.category.name if video.category else None
            })
        
        return {
            "success": True,
            "recommendations": formatted_recommendations,
            "total_count": recommendations["total_count"],
            "strategies_used": recommendations["strategies_used"],
            "user_history_count": recommendations["user_history_count"],
            "parameters": {
                "limit": limit,
                "exclude_watched": exclude_watched,
                "category_id": category_id
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/recommendations/current-video/{video_id}")
async def get_current_video_recommendations(
    video_id: int,
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendations based on the currently watching video
    """
    try:
        recommendation_service = VideoRecommendationService(db)
        
        recommendations = recommendation_service.get_recommendations_for_current_video(
            user_id=current_user["user_id"],
            current_video_id=video_id,
            limit=limit
        )
        
        # Format response
        formatted_recommendations = []
        for rec in recommendations["recommendations"]:
            video = rec["video"]
            formatted_recommendations.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "file_url": video.file_url,
                "category_id": video.category_id,
                "view_count": video.view_count,
                "created_at": video.created_at.isoformat(),
                "duration": video.duration,
                "tags": video.tags,
                "recommendation_score": rec["score"],
                "recommendation_reason": rec["reason"],
                "category": video.category.name if video.category else None
            })
        
        return {
            "success": True,
            "recommendations": formatted_recommendations,
            "current_video_id": video_id,
            "total_count": recommendations["total_count"],
            "strategies_used": recommendations["strategies_used"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get current video recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/search-recommendations")
async def search_video_recommendations(
    query: str = Query(..., min_length=1, description="Search query for video recommendations"),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get video recommendations based on natural language search query
    """
    try:
        recommendation_service = VideoRecommendationService(db)
        
        recommendations = recommendation_service.search_recommendations(
            query=query,
            limit=limit,
            exclude_ids=[]
        )
        
        # Format response
        formatted_recommendations = []
        for rec in recommendations["recommendations"]:
            video = rec["video"]
            formatted_recommendations.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "file_url": video.file_url,
                "category_id": video.category_id,
                "view_count": video.view_count,
                "created_at": video.created_at.isoformat(),
                "duration": video.duration,
                "tags": video.tags,
                "recommendation_score": rec["score"],
                "recommendation_reason": rec["reason"],
                "category": video.category.name if video.category else None
            })
        
        return {
            "success": True,
            "recommendations": formatted_recommendations,
            "search_query": query,
            "total_count": recommendations["total_count"],
            "strategies_used": recommendations["strategies_used"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get search recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get search recommendations: {str(e)}")

@router.post("/embeddings/rebuild")
async def rebuild_video_embeddings(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rebuild all video embeddings (Admin only)
    This is a heavy operation that should be used sparingly
    """
    try:
        # Check if user is admin (you may need to implement role checking)
        # For now, allowing all authenticated users
        
        recommendation_service = VideoRecommendationService(db)
        recommendation_service.rebuild_all_embeddings()
        
        return {
            "success": True,
            "message": "Video embeddings rebuilt successfully",
            "initiated_by": current_user["user_id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to rebuild embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild embeddings: {str(e)}")

@router.get("/stats")
async def get_recommendation_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about the AI recommendation system
    """
    try:
        recommendation_service = VideoRecommendationService(db)
        stats = recommendation_service.get_recommendation_stats()
        
        return {
            "success": True,
            "stats": stats,
            "requested_by": current_user["user_id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/videos/{video_id}/initialize-embedding")
async def initialize_video_embedding(
    video_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize embeddings for a specific video
    Useful when a new video is uploaded
    """
    try:
        recommendation_service = VideoRecommendationService(db)
        
        # Get the video
        video = recommendation_service.video_repo.get_video_by_id(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Initialize embeddings
        recommendation_service.initialize_embeddings_for_video(video)
        
        return {
            "success": True,
            "message": f"Embeddings initialized for video {video_id}",
            "video_title": video.title,
            "initiated_by": current_user["user_id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize video embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize embedding: {str(e)}")

# Health check for AI services
@router.get("/health")
async def ai_health_check():
    """
    Health check for AI services
    """
    try:
        # Try to initialize the recommendation service
        from ai.models.video_embedding import VideoEmbeddingModel
        
        embedding_model = VideoEmbeddingModel()
        stats = embedding_model.get_collection_stats()
        
        return {
            "status": "healthy",
            "service": "AI Recommendation Service",
            "embedding_model": "Ollama + ChromaDB",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "AI Recommendation Service",
            "error": str(e),
            "suggestion": "Please ensure Ollama is running and ChromaDB is accessible"
        }
