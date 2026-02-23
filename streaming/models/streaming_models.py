from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    stream_code = Column(String(6), unique=True, index=True, nullable=False)  # 6-digit public ID
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Multiple streams per user (only one LIVE at a time)
    stream_key = Column(String, unique=True, index=True)
    is_live = Column(Boolean, default=False)
    viewer_count = Column(Integer, default=0)
    max_viewer_count = Column(Integer, default=0)  # Peak concurrent viewers
    thumbnail_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to user
    user = relationship("User", back_populates="streams")

    # Chat messages for the stream
    chat_messages = relationship("StreamChatMessage", back_populates="stream")

class StreamChatMessage(Base):
    __tablename__ = "stream_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    username = Column(String)
    stream_id = Column(Integer, ForeignKey("streams.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stream = relationship("Stream", back_populates="chat_messages")