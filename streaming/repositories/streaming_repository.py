from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from ..models.streaming_models import Stream, StreamChatMessage
import secrets
import string
import random

class StreamingRepository:
    def __init__(self, db: Session):
        self.db = db

    def _generate_stream_code(self) -> str:
        """Generate a unique 6-digit stream code (100000–999999)"""
        while True:
            code = str(random.randint(100000, 999999))
            if not self.db.query(Stream).filter(Stream.stream_code == code).first():
                return code

    def create_stream(self, user_id: int, title: str, description: Optional[str] = None) -> Stream:
        # Generate unique stream key and stream code
        stream_key = self._generate_stream_key()
        stream_code = self._generate_stream_code()

        stream = Stream(
            user_id=user_id,
            title=title,
            description=description,
            stream_key=stream_key,
            stream_code=stream_code
        )
        self.db.add(stream)
        self.db.commit()
        self.db.refresh(stream)
        return stream

    def get_stream_by_id(self, stream_id: int) -> Optional[Stream]:
        return self.db.query(Stream).filter(Stream.id == stream_id).first()

    def get_stream_by_code(self, stream_code: str) -> Optional[Stream]:
        """Look up a stream by its 6-digit public code"""
        return self.db.query(Stream).filter(Stream.stream_code == stream_code).first()

    def get_stream_by_key(self, stream_key: str) -> Optional[Stream]:
        return self.db.query(Stream).filter(Stream.stream_key == stream_key).first()

    def get_user_active_stream(self, user_id: int) -> Optional[Stream]:
        return self.db.query(Stream).filter(
            and_(Stream.user_id == user_id, Stream.is_live == True)
        ).first()

    def get_user_streams(self, user_id: int) -> List[Stream]:
        return self.db.query(Stream).filter(Stream.user_id == user_id).all()

    def update_stream(self, stream: Stream, **kwargs) -> Stream:
        for key, value in kwargs.items():
            if hasattr(stream, key):
                setattr(stream, key, value)
        self.db.commit()
        self.db.refresh(stream)
        return stream

    def delete_stream(self, stream: Stream):
        self.db.delete(stream)
        self.db.commit()

    def start_stream(self, stream: Stream) -> Stream:
        from datetime import datetime
        return self.update_stream(stream, is_live=True, started_at=datetime.utcnow())

    def end_stream(self, stream: Stream) -> Stream:
        from datetime import datetime
        return self.update_stream(stream, is_live=False, ended_at=datetime.utcnow())

    def increment_viewer_count(self, stream: Stream) -> Stream:
        return self.update_stream(stream, viewer_count=stream.viewer_count + 1)

    def decrement_viewer_count(self, stream: Stream) -> Stream:
        new_count = max(0, stream.viewer_count - 1)
        return self.update_stream(stream, viewer_count=new_count)

    def add_chat_message(self, stream_id: int, user_id: int, username: str, message: str) -> StreamChatMessage:
        chat_message = StreamChatMessage(
            stream_id=stream_id,
            user_id=user_id,
            username=username,
            message=message
        )
        self.db.add(chat_message)
        self.db.commit()
        self.db.refresh(chat_message)
        return chat_message

    def get_stream_chat_messages(self, stream_id: int, limit: int = 50) -> List[StreamChatMessage]:
        return self.db.query(StreamChatMessage).filter(
            StreamChatMessage.stream_id == stream_id
        ).order_by(StreamChatMessage.created_at.desc()).limit(limit).all()

    def get_live_streams(self) -> List[Stream]:
        return self.db.query(Stream).filter(Stream.is_live == True).all()

    def _generate_stream_key(self) -> str:
        """Generate a unique stream key"""
        characters = string.ascii_letters + string.digits
        while True:
            key = ''.join(secrets.choice(characters) for _ in range(32))
            if not self.get_stream_by_key(key):
                return key