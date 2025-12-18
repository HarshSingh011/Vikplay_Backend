"""
WebRTC signaling manager for handling peer-to-peer connections in calls.
Manages WebSocket connections and signaling messages for WebRTC.
"""
from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import logging
from datetime import datetime

from call.schemas.call_schemas import (
    WSMessage,
    WSMessageType,
    WebRTCSignal
)

logger = logging.getLogger(__name__)


class CallSignalingManager:
    """
    Manages WebRTC signaling for video calls.
    Handles WebSocket connections and routing of signaling messages.
    """

    def __init__(self):
        # Map of user_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Map of call_id -> set of user_ids in the call
        self.call_participants: Dict[str, Set[str]] = {}
        
        # Map of peer_id -> user_id for WebRTC peer mapping
        self.peer_to_user: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a WebSocket connection for a user.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to call signaling")

    def disconnect(self, user_id: str):
        """
        Remove a user's WebSocket connection.
        
        Args:
            user_id: User ID
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove from all calls
        for call_id in list(self.call_participants.keys()):
            if user_id in self.call_participants[call_id]:
                self.call_participants[call_id].remove(user_id)
                if not self.call_participants[call_id]:
                    del self.call_participants[call_id]
        
        # Remove peer mappings
        peer_ids_to_remove = [
            peer_id for peer_id, uid in self.peer_to_user.items()
            if uid == user_id
        ]
        for peer_id in peer_ids_to_remove:
            del self.peer_to_user[peer_id]
        
        logger.info(f"User {user_id} disconnected from call signaling")

    def add_to_call(self, call_id: str, user_id: str, peer_id: Optional[str] = None):
        """
        Add a user to a call's participant list.
        
        Args:
            call_id: Call ID
            user_id: User ID
            peer_id: Optional WebRTC peer ID
        """
        if call_id not in self.call_participants:
            self.call_participants[call_id] = set()
        
        self.call_participants[call_id].add(user_id)
        
        if peer_id:
            self.peer_to_user[peer_id] = user_id
        
        logger.info(f"User {user_id} added to call {call_id}")

    def remove_from_call(self, call_id: str, user_id: str):
        """
        Remove a user from a call's participant list.
        
        Args:
            call_id: Call ID
            user_id: User ID
        """
        if call_id in self.call_participants:
            self.call_participants[call_id].discard(user_id)
            if not self.call_participants[call_id]:
                del self.call_participants[call_id]
        
        logger.info(f"User {user_id} removed from call {call_id}")

    async def send_to_user(self, user_id: str, message: dict):
        """
        Send a message to a specific user.
        
        Args:
            user_id: Target user ID
            message: Message to send
        """
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Connection might be broken, remove it
                self.disconnect(user_id)

    async def broadcast_to_call(
        self,
        call_id: str,
        message: dict,
        exclude_user_id: Optional[str] = None
    ):
        """
        Broadcast a message to all participants in a call.
        
        Args:
            call_id: Call ID
            message: Message to broadcast
            exclude_user_id: Optional user ID to exclude from broadcast
        """
        if call_id not in self.call_participants:
            return
        
        for user_id in self.call_participants[call_id]:
            if user_id != exclude_user_id:
                await self.send_to_user(user_id, message)

    async def send_webrtc_signal(
        self,
        from_user_id: str,
        to_user_id: str,
        signal_type: str,
        data: dict
    ):
        """
        Send a WebRTC signaling message from one user to another.
        
        Args:
            from_user_id: Sender user ID
            to_user_id: Recipient user ID
            signal_type: Type of signal (offer, answer, ice-candidate)
            data: Signal data
        """
        message = {
            "type": signal_type,
            "from_user_id": from_user_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_to_user(to_user_id, message)
        logger.info(f"WebRTC signal {signal_type} sent from {from_user_id} to {to_user_id}")

    async def notify_participant_joined(
        self,
        call_id: str,
        user_id: str,
        user_info: dict
    ):
        """
        Notify all participants that someone joined the call.
        
        Args:
            call_id: Call ID
            user_id: User ID who joined
            user_info: User information
        """
        message = {
            "type": WSMessageType.PARTICIPANT_JOINED.value,
            "data": {
                "call_id": call_id,
                "user_id": user_id,
                "user_info": user_info
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_call(call_id, message, exclude_user_id=user_id)

    async def notify_participant_left(
        self,
        call_id: str,
        user_id: str
    ):
        """
        Notify all participants that someone left the call.
        
        Args:
            call_id: Call ID
            user_id: User ID who left
        """
        message = {
            "type": WSMessageType.PARTICIPANT_LEFT.value,
            "data": {
                "call_id": call_id,
                "user_id": user_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_call(call_id, message, exclude_user_id=user_id)

    async def notify_call_ended(self, call_id: str):
        """
        Notify all participants that the call has ended.
        
        Args:
            call_id: Call ID
        """
        message = {
            "type": WSMessageType.CALL_ENDED.value,
            "data": {
                "call_id": call_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_call(call_id, message)

    async def notify_incoming_call(
        self,
        user_id: str,
        call_id: str,
        caller_info: dict
    ):
        """
        Notify a user of an incoming call.
        
        Args:
            user_id: User being called
            call_id: Call ID
            caller_info: Information about the caller
        """
        message = {
            "type": WSMessageType.CALL_INITIATED.value,
            "data": {
                "call_id": call_id,
                "caller_info": caller_info
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_to_user(user_id, message)

    def get_call_participants(self, call_id: str) -> Set[str]:
        """
        Get all user IDs in a call.
        
        Args:
            call_id: Call ID
            
        Returns:
            Set of user IDs
        """
        return self.call_participants.get(call_id, set())

    def is_user_online(self, user_id: str) -> bool:
        """
        Check if a user is connected to the signaling server.
        
        Args:
            user_id: User ID
            
        Returns:
            True if connected, False otherwise
        """
        return user_id in self.active_connections


# Global instance
call_signaling_manager = CallSignalingManager()
