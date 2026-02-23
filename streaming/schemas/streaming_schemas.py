from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Stream(BaseModel):
    id: int
    stream_code: str
    title: str
    description: Optional[str] = None
    user_id: int
    stream_key: str
    is_live: bool
    viewer_count: int
    max_viewer_count: int = 0
    thumbnail_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StreamHistory(BaseModel):
    """Lightweight view of a past stream for history listing"""
    id: int
    stream_code: str
    title: str
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    max_viewer_count: int = 0
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class LiveStreamInfo(BaseModel):
    """Public info about a live stream"""
    stream_code: str
    title: str
    description: Optional[str] = None
    user_id: int
    username: Optional[str] = None
    viewer_count: int = 0
    started_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None


class StreamSearchResult(BaseModel):
    """Search result item"""
    stream_code: str
    title: str
    description: Optional[str] = None
    is_live: bool
    viewer_count: int = 0
    max_viewer_count: int = 0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


# ── Chat schemas ──────────────────────────────────────────

class StreamChatMessageBase(BaseModel):
    message: str
    username: str

class StreamChatMessage(StreamChatMessageBase):
    id: int
    user_id: int
    stream_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Request schemas ───────────────────────────────────────

class StreamStartRequest(BaseModel):
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None