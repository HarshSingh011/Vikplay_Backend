from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    user_id = Column(String, index=True)  # ID of the streamer
    stream_key = Column(String, unique=True, index=True)  # Unique key for broadcasting
    thumbnail_url = Column(String, nullable=True)
    is_live = Column(Boolean, default=False)
    viewer_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    chat_messages = relationship("ChatMessage", back_populates="stream")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(Integer, ForeignKey("streams.id"))
    user_id = Column(String, index=True)
    username = Column(String)
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    stream = relationship("Stream", back_populates="chat_messages")