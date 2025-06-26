from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StreamBase(BaseModel):
    title: str
    description: Optional[str] = None

class StreamCreate(StreamBase):
    user_id: str

class Stream(StreamBase):
    id: int
    stream_key: str
    user_id: str
    is_live: bool
    viewer_count: int
    thumbnail_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class StreamPublic(StreamBase):
    id: int
    user_id: str
    is_live: bool
    viewer_count: int
    thumbnail_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    message: str

class ChatMessageCreate(ChatMessageBase):
    user_id: str
    username: str
    stream_id: int

class ChatMessage(ChatMessageBase):
    id: int
    user_id: str
    username: str
    stream_id: int
    created_at: datetime

    class Config:
        from_attributes = True
