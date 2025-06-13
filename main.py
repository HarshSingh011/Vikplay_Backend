import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models.models as models

logging.basicConfig(level=logging.INFO)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Video Server API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers AFTER app is defined
from routes import videos
app.include_router(videos.router)

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