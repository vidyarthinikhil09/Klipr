"""
FastAPI main application for AutoShorts.
Provides REST API endpoints for the React frontend.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import get_settings
from .api import clips, videos, upload, analytics, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    os.makedirs(settings.temp_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)
    print(f"🚀 {settings.app_name} starting...")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="AutoShorts API",
    description="AI-powered Twitch clip to YouTube Shorts automation",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration for React frontend
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for video previews
if os.path.exists("output"):
    app.mount("/videos", StaticFiles(directory="output"), name="videos")
if os.path.exists("temp"):
    app.mount("/temp", StaticFiles(directory="temp"), name="temp")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clips.router, prefix="/api/clips", tags=["Clips"])
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "app": "AutoShorts API",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    settings = get_settings()
    return {
        "status": "healthy",
        "services": {
            "twitch": bool(settings.twitch_client_id),
            "openrouter": bool(settings.openrouter_api_key),
            "pexels": bool(settings.pexels_api_key),
            "youtube": bool(settings.youtube_client_id),
            "supabase": bool(settings.supabase_url)
        }
    }


@app.get("/api/config")
async def get_config():
    """Get public configuration for frontend."""
    from .config import CREATORS, GAMES, HOOK_STYLES
    return {
        "creators": CREATORS,
        "games": GAMES,
        "hook_styles": HOOK_STYLES
    }
