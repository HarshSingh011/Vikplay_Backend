from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import videos  # Remove the dot for regular imports
from database import engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Video Server API")

app.mount("/static", StaticFiles(directory="static"), name="static")  # Match the path in videos.py

app.include_router(videos.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)