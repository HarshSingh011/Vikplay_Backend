from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from schemas.streaming import Stream, StreamCreate, StreamPublic, ChatMessage

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    file_url: str
    created_at: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode = True
