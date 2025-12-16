from sqlalchemy.orm import Session
from typing import List, Optional
from ..repositories.streaming_repository import StreamingRepository
from ..schemas.streaming_schemas import StreamCreate, StreamUpdateRequest
from ..models.streaming_models import Stream
from fastapi import HTTPException, status

class StreamingService:
    def __init__(self, db: Session):
        self.repository = StreamingRepository(db)

    def create_stream(self, user_id: int, stream_data: StreamCreate) -> dict:
        # Check if user already has an active stream
        active_stream = self.repository.get_user_active_stream(user_id)
        if active_stream:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active stream. Only one stream per user is allowed."
            )

        stream = self.repository.create_stream(
            user_id=user_id,
            title=stream_data.title,
            description=stream_data.description
        )

        return {
            "stream": stream,
            "stream_key": stream.stream_key,
            "message": "Stream created successfully. Use the stream key for broadcasting."
        }

    def get_stream(self, stream_id: int) -> Optional[dict]:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            return None
        return {"stream": stream}

    def get_user_streams(self, user_id: int) -> List[dict]:
        streams = self.repository.get_user_streams(user_id)
        return [{"stream": stream} for stream in streams]

    def update_stream(self, stream_id: int, user_id: int, update_data: StreamUpdateRequest) -> dict:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this stream")

        # Prevent updating live status directly through this endpoint
        update_dict = update_data.model_dump(exclude_unset=True)
        if 'is_live' in update_dict:
            del update_dict['is_live']

        updated_stream = self.repository.update_stream(stream, **update_dict)
        return {"stream": updated_stream, "message": "Stream updated successfully"}

    def delete_stream(self, stream_id: int, user_id: int) -> dict:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this stream")

        if stream.is_live:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete an active stream. End the stream first."
            )

        self.repository.delete_stream(stream)
        return {"message": "Stream deleted successfully"}

    def start_stream(self, stream_id: int, user_id: int) -> dict:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to start this stream")

        if stream.is_live:
            raise HTTPException(status_code=400, detail="Stream is already live")

        # Check if user has another active stream
        active_stream = self.repository.get_user_active_stream(user_id)
        if active_stream and active_stream.id != stream_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active stream. Only one stream per user is allowed."
            )

        updated_stream = self.repository.start_stream(stream)
        return {"stream": updated_stream, "message": "Stream started successfully"}

    def end_stream(self, stream_id: int, user_id: int) -> dict:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        if stream.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to end this stream")

        if not stream.is_live:
            raise HTTPException(status_code=400, detail="Stream is not live")

        updated_stream = self.repository.end_stream(stream)
        return {"stream": updated_stream, "message": "Stream ended successfully"}

    def get_live_streams(self) -> List[Stream]:
        streams = self.repository.get_live_streams()
        return streams

    def add_chat_message(self, stream_id: int, user_id: int, username: str, message: str) -> dict:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        if not stream.is_live:
            raise HTTPException(status_code=400, detail="Cannot send messages to inactive streams")

        chat_message = self.repository.add_chat_message(stream_id, user_id, username, message)
        return {"chat_message": chat_message, "message": "Message sent successfully"}

    def get_stream_chat(self, stream_id: int, limit: int = 50) -> List[dict]:
        stream = self.repository.get_stream_by_id(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        messages = self.repository.get_stream_chat_messages(stream_id, limit)
        return [{"chat_message": msg} for msg in messages]