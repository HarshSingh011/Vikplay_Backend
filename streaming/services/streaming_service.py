from sqlalchemy.orm import Session
from typing import List, Optional
from ..repositories.streaming_repository import StreamingRepository
from ..schemas.streaming_schemas import StreamStartRequest
from ..models.streaming_models import Stream
from fastapi import HTTPException, status


class StreamingService:
    def __init__(self, db: Session):
        self.repository = StreamingRepository(db)

    # ── Internal helpers (used by webrtc_routes) ─────────

    def get_stream(self, stream_id: int) -> Optional[dict]:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            return None
        return {"stream": stream}

    def get_stream_by_code(self, stream_code: str) -> Optional[dict]:
        """Look up a stream by its 6-digit public code"""
        stream = self.repository.get_stream_by_code(stream_code)
        if not stream:
            return None
        return {"stream": stream}

    def start_stream(self, stream_id: int, user_id: int) -> dict:
        """Mark a stream as live (called by webrtc broadcast handler)."""
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if stream.is_live:
            return {"stream": stream, "message": "Stream is already live"}
        active = self.repository.get_user_active_stream(user_id)
        if active and active.id != stream_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a live stream.",
            )
        updated = self.repository.start_stream(stream)
        return {"stream": updated, "message": "Stream started"}

    def end_stream(self, stream_id: int, user_id: int) -> dict:
        """Mark a stream as offline (called by webrtc broadcast handler)."""
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if not stream.is_live:
            return {"stream": stream, "message": "Stream is already offline"}
        updated = self.repository.end_stream(stream)
        return {"stream": updated, "message": "Stream ended"}

    # ── Public REST endpoints ────────────────────────────

    def quick_start_stream(self, user_id: int, data: StreamStartRequest) -> dict:
        """Create a stream AND immediately go live.
        Enforces one live stream per user."""
        active = self.repository.get_user_active_stream(user_id)
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a live stream. End it before starting a new one.",
            )
        stream = self.repository.create_stream(
            user_id=user_id,
            title=data.title,
            description=data.description,
            thumbnail_url=data.thumbnail_url,
        )
        started = self.repository.start_stream(stream)
        return {
            "stream_code": started.stream_code,
            "title": started.title,
            "description": started.description,
            "thumbnail_url": started.thumbnail_url,
            "stream_key": started.stream_key,
            "started_at": started.started_at.isoformat() if started.started_at else None,
            "message": "Stream created and is now LIVE.",
        }

    def end_stream_by_code(self, stream_code: str, user_id: int) -> dict:
        """End a live stream using its 6-digit code (owner only)."""
        stream = self.repository.get_stream_by_code(stream_code)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to end this stream")
        if not stream.is_live:
            raise HTTPException(status_code=400, detail="Stream is not live")
        updated = self.repository.end_stream(stream)
        return {
            "stream_code": updated.stream_code,
            "ended_at": updated.ended_at.isoformat() if updated.ended_at else None,
            "message": "Stream ended successfully",
        }

    def get_live_streams(self) -> List[Stream]:
        return self.repository.get_live_streams()

    def get_stream_history(self, user_id: int) -> List[dict]:
        """All past streams for a user with duration & peak viewers."""
        streams = self.repository.get_user_stream_history(user_id)
        result = []
        for s in streams:
            duration = None
            if s.started_at and s.ended_at:
                duration = int((s.ended_at - s.started_at).total_seconds())
            result.append({
                "id": s.id,
                "stream_code": s.stream_code,
                "title": s.title,
                "description": s.description,
                "thumbnail_url": s.thumbnail_url,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "duration_seconds": duration,
                "max_viewer_count": s.max_viewer_count or 0,
                "is_live": s.is_live,
            })
        return result

    def search_streams(self, query: str, live_only: bool = False) -> List[dict]:
        """Search streams by title/description."""
        streams = self.repository.search_streams(query, live_only)
        result = []
        for s in streams:
            duration = None
            if s.started_at and s.ended_at:
                duration = int((s.ended_at - s.started_at).total_seconds())
            result.append({
                "stream_code": s.stream_code,
                "title": s.title,
                "description": s.description,
                "is_live": s.is_live,
                "viewer_count": s.viewer_count or 0,
                "max_viewer_count": s.max_viewer_count or 0,
                "thumbnail_url": s.thumbnail_url,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "duration_seconds": duration,
            })
        return result

    def get_chat_by_stream_code(self, stream_code: str, limit: int = 100) -> List[dict]:
        """Chat messages for a stream using its public stream_code."""
        stream = self.repository.get_stream_by_code(stream_code)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        messages = self.repository.get_stream_chat_messages(stream.id, limit)
        return [{"chat_message": msg} for msg in messages]