from fastapi import APIRouter
from .streaming_routes import router as streaming_router
from .webrtc_routes import router as webrtc_router
from .chat_docs import router as chat_docs_router

# Create a main router that includes all streaming-related routers
main_router = APIRouter()
main_router.include_router(streaming_router)
main_router.include_router(webrtc_router)
main_router.include_router(chat_docs_router)

__all__ = ["streaming_router", "webrtc_router", "chat_docs_router", "main_router"]

# Export main_router as the default router
router = main_router