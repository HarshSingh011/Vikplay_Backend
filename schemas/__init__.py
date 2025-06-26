# Legacy schemas __init__.py file
# Video schemas have been moved to video.schemas
# Only streaming schemas remain here

# Import streaming schemas
from .streaming import StreamBase, StreamCreate, Stream, StreamPublic, ChatMessageBase, ChatMessageCreate, ChatMessage

# Make streaming schemas available at the top level
__all__ = [
    'StreamBase', 'StreamCreate', 'Stream', 'StreamPublic',
    'ChatMessageBase', 'ChatMessageCreate', 'ChatMessage'
]