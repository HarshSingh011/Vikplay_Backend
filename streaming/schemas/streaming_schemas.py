from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

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


# ══════════════════════════════════════════════════════════
# Typed response schemas — shown in Swagger /docs
# ══════════════════════════════════════════════════════════

class StreamStartResponse(BaseModel):
    """Response after calling POST /api/streaming/streams/start"""
    stream_code: str = Field(..., example="A1B2C3", description="6-digit public code — share with viewers")
    title: str = Field(..., example="My Gaming Stream")
    description: Optional[str] = Field(None, example="Playing Minecraft live!")
    thumbnail_url: Optional[str] = Field(None, example="https://example.com/thumb.jpg")
    stream_key: str = Field(..., example="sk_abc123xyz", description="Private key (for OBS etc)")
    started_at: Optional[str] = Field(None, example="2026-02-24T10:00:00Z")
    message: str = Field(..., example="Stream created and is now LIVE.")


class StreamEndResponse(BaseModel):
    """Response after calling POST /api/streaming/streams/end/{stream_code}"""
    stream_code: str = Field(..., example="A1B2C3")
    ended_at: Optional[str] = Field(None, example="2026-02-24T11:30:00Z")
    message: str = Field(..., example="Stream ended successfully")


class LiveStreamItem(BaseModel):
    """A single live stream returned by GET /api/streaming/streams/live"""
    stream_code: str = Field(..., example="A1B2C3")
    title: str = Field(..., example="Epic Gaming Stream")
    description: Optional[str] = Field(None, example="Watch me play Minecraft!")
    user_id: int = Field(..., example=42)
    viewer_count: int = Field(0, example=125)
    thumbnail_url: Optional[str] = Field(None, example="https://example.com/thumb.jpg")
    started_at: Optional[str] = Field(None, example="2026-02-24T10:00:00Z")


class StreamDetail(BaseModel):
    """Full stream object (nested inside StreamDetailResponse)"""
    id: int = Field(..., example=7)
    stream_code: str = Field(..., example="A1B2C3")
    title: str = Field(..., example="Epic Gaming Stream")
    description: Optional[str] = Field(None, example="Watch me play!")
    user_id: int = Field(..., example=42)
    stream_key: str = Field(..., example="sk_abc123xyz")
    is_live: bool = Field(..., example=True)
    viewer_count: int = Field(0, example=125)
    max_viewer_count: int = Field(0, example=200)
    thumbnail_url: Optional[str] = Field(None, example="https://example.com/thumb.jpg")
    created_at: Optional[str] = Field(None, example="2026-02-24T09:55:00Z")
    started_at: Optional[str] = Field(None, example="2026-02-24T10:00:00Z")
    ended_at: Optional[str] = Field(None, example=None)


class StreamDetailResponse(BaseModel):
    """Response for GET /api/streaming/streams/code/{stream_code}"""
    stream: StreamDetail


class StreamHistoryItem(BaseModel):
    """A single past stream returned by GET /api/streaming/streams/history/me"""
    id: int = Field(..., example=7)
    stream_code: str = Field(..., example="A1B2C3")
    title: str = Field(..., example="Epic Gaming Stream")
    description: Optional[str] = Field(None, example="Watch me play!")
    thumbnail_url: Optional[str] = Field(None, example="https://example.com/thumb.jpg")
    started_at: Optional[str] = Field(None, example="2026-02-24T10:00:00Z")
    ended_at: Optional[str] = Field(None, example="2026-02-24T11:30:00Z")
    duration_seconds: Optional[int] = Field(None, example=5400, description="Total stream length in seconds")
    max_viewer_count: int = Field(0, example=200, description="Peak concurrent viewers")
    is_live: bool = Field(False, example=False)


class StreamSearchItem(BaseModel):
    """A single result from GET /api/streaming/streams/search"""
    stream_code: str = Field(..., example="A1B2C3")
    title: str = Field(..., example="Epic Gaming Stream")
    description: Optional[str] = Field(None, example="Watch me play!")
    is_live: bool = Field(..., example=True)
    viewer_count: int = Field(0, example=125)
    max_viewer_count: int = Field(0, example=200)
    thumbnail_url: Optional[str] = Field(None, example="https://example.com/thumb.jpg")
    started_at: Optional[str] = Field(None, example="2026-02-24T10:00:00Z")
    ended_at: Optional[str] = Field(None, example=None)
    duration_seconds: Optional[int] = Field(None, example=None)


class ChatMessageResponse(BaseModel):
    """A single chat message returned by GET /api/streaming/streams/code/{stream_code}/chat"""
    id: int = Field(..., example=101)
    user_id: int = Field(..., example=42)
    username: str = Field(..., example="Alice")
    message: str = Field(..., example="Hello viewers!")
    created_at: Optional[str] = Field(None, example="2026-02-24T10:05:00Z")


# ── WebSocket chat documentation schemas ──────────────────

class WsChatSendSchema(BaseModel):
    """JSON you send over WebSocket to broadcast a chat message"""
    type: str = Field(
        "chat_message",
        example="chat_message",
        description="Always 'chat_message' for chat. Other allowed types: offer, answer, ice_candidate, ping"
    )
    username: str = Field(..., example="Alice", description="Your display name shown in the chat")
    message: str = Field(..., example="Hello viewers!", description="The chat text to send")


class WsChatReceiveSchema(BaseModel):
    """JSON received over WebSocket when someone sends a chat message"""
    type: str = Field("chat_message", example="chat_message")
    username: str = Field(..., example="Bob", description="Display name of the sender")
    message: str = Field(..., example="Nice stream!", description="Chat message text")
    role: str = Field(..., example="viewer", description="'broadcaster' or 'viewer'")


class WsBroadcasterConnectResponse(BaseModel):
    """Shows how to connect to the broadcaster WebSocket and send chat"""
    ws_endpoint: str = Field(
        ...,
        example="ws://HOST/api/webrtc/ws/broadcast/A1B2C3?token=YOUR_TOKEN"
    )
    token_required: bool = Field(True, description="Bearer token MUST be passed as ?token= query param")
    query_params: Dict[str, Any] = Field(
        ...,
        example={"token": "required — your JWT access_token from POST /auth/login"}
    )
    send_message_types: List[str] = Field(
        ...,
        example=["chat_message", "answer", "ice_candidate", "sync_timestamp", "ping"]
    )
    receive_message_types: List[str] = Field(
        ...,
        example=["chat_message", "offer", "ice_candidate", "pong"]
    )
    example_chat_payload: Dict[str, Any] = Field(
        ...,
        example={"type": "chat_message", "username": "Alice", "message": "Hello viewers!"}
    )


class WsViewerConnectResponse(BaseModel):
    """Shows how to connect to the viewer WebSocket and send chat"""
    ws_endpoint: str = Field(
        ...,
        example="ws://HOST/api/webrtc/ws/view/A1B2C3"
    )
    token_required: bool = Field(False, description="Token is optional — anonymous viewers are allowed")
    query_params: Dict[str, Any] = Field(
        ...,
        example={"token": "optional — include to authenticate as a registered user"}
    )
    send_message_types: List[str] = Field(
        ...,
        example=["chat_message", "offer", "ice_candidate", "request_go_live", "ping"]
    )
    receive_message_types: List[str] = Field(
        ...,
        example=["chat_message", "answer", "ice_candidate", "pong"]
    )
    example_chat_payload: Dict[str, Any] = Field(
        ...,
        example={"type": "chat_message", "username": "Bob", "message": "Nice stream!"}
    )