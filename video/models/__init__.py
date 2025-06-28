"""
Video Models - Database models for video functionality
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Import these from the main models for consistency
from models.models import Video, Category, UserVideoHistory, UserPreferences

__all__ = ["Video", "Category", "UserVideoHistory", "UserPreferences"]
