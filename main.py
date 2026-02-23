import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from database import engine
import os

# Import all models to register them with SQLAlchemy
import auth.models as auth_models  # Auth models
import video.models.video_models as video_models  # Video models
import streaming.models.streaming_models as streaming_models  # Streaming models
import call.models.call_models as call_models  # Call models

# Load environment variables - override system env vars
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all tables including all module tables
auth_models.Base.metadata.create_all(bind=engine)
video_models.Base.metadata.create_all(bind=engine)
streaming_models.Base.metadata.create_all(bind=engine)
call_models.Base.metadata.create_all(bind=engine)  # Enabled for calls

app = FastAPI(title="Video Server API", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Health check endpoint for Docker/Kubernetes
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {"status": "healthy", "service": "VikPay Backend", "version": "1.0.0"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to VikPay Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

# Include routers AFTER app is defined
# Video module
try:
    from video import router as video_router
    app.include_router(video_router)
    logging.info("Video router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load video router: {e}")

# AI module
try:
    from ai import router as ai_router
    app.include_router(ai_router)
    logging.info("AI router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load AI router: {e}")

# Authentication routes
try:
    from auth import router as auth_router  
    app.include_router(auth_router)
    logging.info("Auth router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load auth router: {e}")

# Streaming routes
try:
    from streaming import router as streaming_router
    app.include_router(streaming_router)
    logging.info("Streaming router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load streaming router: {e}")

# Call routes
try:
    from call.routes import call_router
    app.include_router(call_router)
    logging.info("Call router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load call router: {e}")

# Serve HTML files for WebRTC testing
@app.get("/broadcaster_jwt.html")
async def serve_broadcaster_jwt():
    """Serve the JWT broadcaster HTML page"""
    return FileResponse("broadcaster_jwt.html")

@app.get("/viewer_jwt.html")
async def serve_viewer_jwt():
    """Serve the JWT viewer HTML page"""
    return FileResponse("viewer_jwt.html")

@app.get("/whatsapp_call_test.html")
async def serve_whatsapp_call_test():
    """Serve the WhatsApp call test HTML page"""
    return FileResponse("whatsapp_call_test.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
    )