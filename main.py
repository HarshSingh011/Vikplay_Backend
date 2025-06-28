import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models.models as models
import auth.models as auth_models  # Import auth models to register them

# Load environment variables - override system env vars
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all tables including auth tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="VikPay Video Platform API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint for Docker/Kubernetes
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {"status": "healthy", "service": "VikPay Backend", "version": "2.0.0"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to VikPay Video Platform API",
        "version": "2.0.0",
        "features": [
            "Video Management",
            "User Authentication", 
            "AI-Powered Recommendations",
            "WebRTC Streaming",
            "User History Tracking"
        ],
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

# Include routers AFTER app is defined
from routes import videos
app.include_router(videos.router)

# Include video module routes
try:
    from video.routes.video_routes import router as video_router
    app.include_router(video_router)
    logging.info("Video router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load video router: {e}")

# Include AI recommendation routes
try:
    from ai.routes.ai_routes import router as ai_router
    app.include_router(ai_router)
    logging.info("AI router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load AI router: {e}")

# Include authentication routes
try:
    from auth import router as auth_router
    app.include_router(auth_router)
    logging.info("Auth router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load auth router: {e}")

try:
    from routes import streaming
    app.include_router(streaming.router)
    logging.info("Streaming router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load streaming router: {e}")

try:
    from routes import webrtc
    app.include_router(webrtc.router)
    logging.info("WebRTC router loaded successfully")
except Exception as e:
    logging.error(f"Failed to load WebRTC router: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
    )