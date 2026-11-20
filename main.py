import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from aura.config import settings, BASE_DIR
from aura.routes import router
from aura.firebase_service import init_firebase

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Firebase if credentials provided
    init_firebase()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_SUBTITLE,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
