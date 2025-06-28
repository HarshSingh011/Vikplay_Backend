"""
AI Module - AI-powered video recommendations using Ollama + ChromaDB

This module provides:
- Content-based filtering using video embeddings
- Collaborative filtering based on user behavior
- Category-based recommendations
- Trending video recommendations
- Natural language search for videos

Technologies used:
- Ollama: For generating embeddings and AI processing
- ChromaDB: For vector storage and similarity search
- FastAPI: For API endpoints
- SQLAlchemy: For database operations

Usage:
1. Ensure Ollama is installed and running
2. The system will automatically pull required models
3. Video embeddings are generated automatically
4. Users get personalized recommendations based on their history
"""

from .models.video_embedding import VideoEmbeddingModel
from .services.recommendation_service import VideoRecommendationService
from .routes.ai_routes import router as ai_router

__all__ = [
    "VideoEmbeddingModel",
    "VideoRecommendationService", 
    "ai_router"
]
