from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StreamBase(BaseModel):
    title: str
    description: Optional[str] = None
    user_id: str

class StreamCreate(StreamBase):
    pass

class Stream(StreamBase):
    id: int
    stream_key: str
    is_live: bool
    viewer_count: int
    thumbnail_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    message: str
    user_id: str
    username: str
    stream_id: int

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class WebRTCOfferRequest(BaseModel):
    sdp: str
    type: str = "offer"
    stream_id: Optional[str] = None
    client_id: Optional[str] = None
    is_broadcaster: bool = False

class WebRTCAnswerRequest(BaseModel):
    sdp: str
    type: str = "answer"
    stream_id: str
    client_id: str

class WebRTCICECandidate(BaseModel):
    candidate: str
    sdp_mid: Optional[str] = None
    sdp_mline_index: Optional[int] = None
    stream_id: str
    client_id: str
