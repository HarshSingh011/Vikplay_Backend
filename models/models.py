from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Import auth models
from auth.models import User, OTP

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
    
    # Relationship with category
    category = relationship("Category", back_populates="videos")

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