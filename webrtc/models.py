from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

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
