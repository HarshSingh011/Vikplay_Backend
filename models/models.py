from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Note: Auth models (User, OTP) are defined in auth/models.py

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    videos = relationship("Video", back_populates="category")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    file_url = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    view_count = Column(Integer, default=0)
    duration = Column(Float, nullable=True)  # Duration in seconds
    tags = Column(Text, nullable=True)  # Comma-separated tags for better AI recommendations
    
    # Relationship with category
    category = relationship("Category", back_populates="videos")
    # Relationship with user history
    user_histories = relationship("UserVideoHistory", back_populates="video")

class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    user_id = Column(String, index=True)
    stream_key = Column(String, unique=True, index=True)
    is_live = Column(Boolean, default=False)
    viewer_count = Column(Integer, default=0)
    thumbnail_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text)
    user_id = Column(String, index=True)
    username = Column(String)
    stream_id = Column(Integer, ForeignKey("streams.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    stream = relationship("Stream")

class UserVideoHistory(Base):
    __tablename__ = "user_video_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # From auth system
    video_id = Column(Integer, ForeignKey("videos.id"))
    watched_at = Column(DateTime(timezone=True), server_default=func.now())
    watch_duration = Column(Float, default=0.0)  # How long user watched in seconds
    completion_percentage = Column(Float, default=0.0)  # Percentage of video watched
    rating = Column(Integer, nullable=True)  # 1-5 star rating (optional)
    liked = Column(Boolean, nullable=True)  # Like/dislike (optional)
    
    # Relationships
    video = relationship("Video", back_populates="user_histories")

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    preferred_categories = Column(Text, nullable=True)  # JSON string of category IDs
    disliked_categories = Column(Text, nullable=True)  # JSON string of category IDs
    preferred_duration_min = Column(Float, nullable=True)  # Minimum preferred duration
    preferred_duration_max = Column(Float, nullable=True)  # Maximum preferred duration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())