"""
Video Models - Database models for video functionality
Re-exports from main models file for consistency
"""
from models.models import Video, Category, UserVideoHistory, UserPreferences

__all__ = ["Video", "Category", "UserVideoHistory", "UserPreferences"]
