"""
AI recommendation schemas for request/response models
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Request schemas
class RecommendationRequest(BaseModel):
    """Schema for recommendation request"""
    user_id: int
    strategy: str = Field("hybrid", description="Recommendation strategy")
    limit: int = Field(10, ge=1, le=50)
    categories: Optional[List[int]] = None
    exclude_watched: bool = True

class UserInteractionRequest(BaseModel):
    """Schema for user interaction tracking"""
    user_id: int
    video_id: int
    interaction_type: str = Field(..., description="Type of interaction: view, like, share, rate")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    watch_duration: Optional[int] = Field(None, ge=0, description="Watch duration in seconds")
    position: Optional[int] = Field(None, ge=0, description="Last watch position in seconds")

class VideoEmbeddingRequest(BaseModel):
    """Schema for video embedding creation"""
    video_id: int
    force_refresh: bool = False

# Response schemas
class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    video_id: int
    title: str
    description: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score")
    reason: str = Field(..., description="Reason for recommendation")
    strategy: str = Field(..., description="Strategy used for recommendation")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True

class SimilarVideoResponse(BaseModel):
    """Schema for similar video response"""
    video_id: int
    title: str
    description: Optional[str] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    reason: str

class AnalyticsResponse(BaseModel):
    """Schema for analytics response"""
    user_id: int
    total_recommendations: int = 0
    strategy_breakdown: Dict[str, int] = Field(default_factory=dict)
    accuracy_metrics: Dict[str, float] = Field(default_factory=dict)
    last_updated: str
    
    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    user_id: int
    preferences: Dict[str, Any] = Field(default_factory=dict)
    watch_history_count: int = 0
    category_preferences: Dict[str, float] = Field(default_factory=dict)
    embedding_status: str = "not_generated"
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RecommendationFeedbackRequest(BaseModel):
    """Schema for recommendation feedback"""
    user_id: int
    video_id: int
    recommendation_id: Optional[str] = None
    feedback: str = Field(..., description="Feedback: like, dislike, not_interested")
    reason: Optional[str] = None

class BatchRecommendationRequest(BaseModel):
    """Schema for batch recommendation request"""
    user_ids: List[int]
    strategy: str = "hybrid"
    limit: int = Field(10, ge=1, le=50)

class BatchRecommendationResponse(BaseModel):
    """Schema for batch recommendation response"""
    user_id: int
    recommendations: List[RecommendationResponse]
    
    class Config:
        from_attributes = True
