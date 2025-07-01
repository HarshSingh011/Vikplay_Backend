"""
Video models for the VikPay Backend
Includes all automatic data collection models for AI recommendations
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    videos = relationship("Video", back_populates="category")


class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    
    # Enhanced metadata for AI
    duration = Column(Integer, nullable=True)  # seconds
    language = Column(String(50), default="english")
    difficulty_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    content_rating = Column(String(10), default="G")  # G, PG, PG-13, R
    tags = Column(JSON, nullable=True)  # ["tutorial", "python", "beginner"]
    
    # Category relationship
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="videos")
    
    # Engagement metrics (automatically updated)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    dislike_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # AI-specific metrics
    average_watch_time = Column(Float, default=0.0)  # average seconds watched
    completion_rate = Column(Float, default=0.0)  # average completion percentage
    engagement_score = Column(Float, default=0.0)  # calculated engagement metric
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    video_history = relationship("UserVideoHistory", back_populates="video")
    search_results = relationship("UserSearchHistory", back_populates="clicked_video")


class UserVideoHistory(Base):
    """
    AUTOMATIC COLLECTION: Viewing History
    Tracks what users watch, when, and for how long
    """
    __tablename__ = "user_video_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    # Viewing data (automatically collected)
    watched_at = Column(DateTime(timezone=True), server_default=func.now())
    watch_duration = Column(Integer, nullable=False)  # seconds watched
    completion_percentage = Column(Float, nullable=False)  # % of video completed
    
    # Engagement data (automatically collected)
    rating = Column(Integer, nullable=True)  # 1-5 stars (if user rates)
    liked = Column(Boolean, nullable=True)  # True=like, False=dislike, None=no action
    shared = Column(Boolean, default=False)  # if user shared
    bookmarked = Column(Boolean, default=False)  # if user bookmarked
    
    # Session context (automatically collected)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    session_id = Column(String(100), nullable=True)  # to track session patterns
    
    # Relationships
    video = relationship("Video", back_populates="video_history")


class UserSearchHistory(Base):
    """
    AUTOMATIC COLLECTION: Search Queries
    Tracks what users search for and what they click
    """
    __tablename__ = "user_search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Search data (automatically collected)
    search_query = Column(String(500), nullable=False, index=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Results interaction (automatically collected)
    results_count = Column(Integer, default=0)  # how many results were shown
    clicked_video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)  # which video they clicked
    click_position = Column(Integer, nullable=True)  # position of clicked result (1st, 2nd, etc.)
    time_to_click = Column(Float, nullable=True)  # seconds from search to click
    
    # Search context
    search_filters = Column(JSON, nullable=True)  # any filters applied
    device_type = Column(String(50), nullable=True)
    
    # Relationships
    clicked_video = relationship("Video", back_populates="search_results")


class UserSession(Base):
    """
    AUTOMATIC COLLECTION: Session Patterns
    Tracks when and how users use the platform
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Session timing (automatically collected)
    session_start = Column(DateTime(timezone=True), server_default=func.now())
    session_end = Column(DateTime(timezone=True), nullable=True)
    session_duration = Column(Integer, nullable=True)  # total seconds
    
    # Session activity (automatically collected)
    videos_watched = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    videos_liked = Column(Integer, default=0)
    videos_shared = Column(Integer, default=0)
    
    # Session context (automatically collected)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet, tv
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # for location/analytics
    user_agent = Column(Text, nullable=True)
    
    # Behavioral patterns (automatically calculated)
    time_of_day = Column(String(20), nullable=True)  # morning, afternoon, evening, night
    day_of_week = Column(String(20), nullable=True)  # monday, tuesday, etc.
    is_weekend = Column(Boolean, default=False)


class UserPreferences(Base):
    """
    User preferences - mix of explicit input and automatic learning
    """
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Explicit preferences (user input)
    preferred_categories = Column(JSON, nullable=True)  # ["technology", "music"]
    disliked_categories = Column(JSON, nullable=True)  # ["horror", "politics"]
    preferred_duration_min = Column(Integer, nullable=True)
    preferred_duration_max = Column(Integer, nullable=True)
    preferred_languages = Column(JSON, nullable=True)  # ["english", "hindi"]
    content_rating_preference = Column(String(10), default="G")
    
    # Automatically learned preferences (from behavior)
    auto_preferred_categories = Column(JSON, nullable=True)  # learned from viewing history
    auto_preferred_duration = Column(Integer, nullable=True)  # learned average preference
    auto_preferred_times = Column(JSON, nullable=True)  # when they usually watch
    auto_engagement_patterns = Column(JSON, nullable=True)  # what engages them most
    
    # Content filters
    mature_content_allowed = Column(Boolean, default=False)
    violence_filter = Column(Boolean, default=False)
    profanity_filter = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class VideoInteractionLog(Base):
    """
    AUTOMATIC COLLECTION: Detailed Engagement Metrics
    Tracks every interaction users have with videos
    """
    __tablename__ = "video_interaction_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    session_id = Column(String(100), nullable=True)
    
    # Interaction details (automatically collected)
    interaction_type = Column(String(50), nullable=False)  # play, pause, seek, like, share, etc.
    interaction_value = Column(String(200), nullable=True)  # specific value (like timestamp for seek)
    interaction_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Context
    video_timestamp = Column(Integer, nullable=True)  # where in video this happened
    device_type = Column(String(50), nullable=True)
