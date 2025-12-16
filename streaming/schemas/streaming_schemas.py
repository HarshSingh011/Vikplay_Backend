from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StreamBase(BaseModel):
    title: str
    description: Optional[str] = None

class StreamCreate(StreamBase):
    pass

class Stream(StreamBase):
    id: int
    user_id: int
    stream_key: str
    is_live: bool
    viewer_count: int
    thumbnail_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StreamChatMessageBase(BaseModel):
    message: str
    username: str

class StreamChatMessageCreate(StreamChatMessageBase):
    pass

class StreamChatMessage(StreamChatMessageBase):
    id: int
    user_id: int
    stream_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class StreamStartRequest(BaseModel):
    title: str
    description: Optional[str] = None

class StreamUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_live: Optional[bool] = None