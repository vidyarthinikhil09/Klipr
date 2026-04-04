"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== User ====================

class User(BaseModel):
    """User model from Supabase Auth."""
    id: str
    email: str
    created_at: Optional[datetime] = None


class UserToken(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


# ==================== Clips ====================

class ClipDiscoveryRequest(BaseModel):
    """Request to discover clips."""
    mode: str = Field(default="creator", description="'creator', 'game', or 'niche'")
    creator: Optional[str] = Field(default=None, description="Specific creator name")
    game: Optional[str] = Field(default=None, description="Specific game name")
    niche: Optional[str] = Field(default=None, description="Specific niche name")
    auto: bool = Field(default=True, description="Auto-select best clip")


class Clip(BaseModel):
    """Twitch clip data."""
    id: str
    url: str
    embed_url: str
    broadcaster_name: str
    title: str
    view_count: int
    duration: float
    thumbnail_url: str
    created_at: str
    game_id: Optional[str] = None


class ClipResponse(BaseModel):
    """Response with discovered clip."""
    success: bool
    clip: Optional[Clip] = None
    message: Optional[str] = None
    local_path: Optional[str] = None


# ==================== Videos ====================

class VideoGenerateRequest(BaseModel):
    """Request to generate a video."""
    clip_url: str
    creator: str
    title_override: Optional[str] = None
    description_override: Optional[str] = None
    caption_style: str = Field(default="mrbeast", description="Caption style: mrbeast, hormozi, tiktok, karaoke, minimalist, classic")


class VideoMetadata(BaseModel):
    """AI-generated video metadata."""
    title: str
    description: str
    tags: List[str]
    hook_style: str
    model_used: str


class Video(BaseModel):
    """Generated video data."""
    id: str
    youtube_id: Optional[str] = None
    title: str
    description: str
    tags: List[str]
    creator: str
    clip_url: str
    hook_style: Optional[str] = None
    model_used: Optional[str] = None
    views: int = 0
    likes: int = 0
    watch_time_pct: float = 0
    ctr: float = 0
    score: float = 0
    status: str = "draft"
    local_path: Optional[str] = None
    created_at: Optional[datetime] = None


class VideoGenerateResponse(BaseModel):
    """Response after video generation."""
    success: bool
    video: Optional[Video] = None
    message: Optional[str] = None
    preview_url: Optional[str] = None


# ==================== Upload ====================

class UploadRequest(BaseModel):
    """Request to upload video to YouTube."""
    video_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class UploadResponse(BaseModel):
    """Response after YouTube upload."""
    success: bool
    youtube_id: Optional[str] = None
    youtube_url: Optional[str] = None
    message: Optional[str] = None


# ==================== Analytics ====================

class AnalyticsRefreshRequest(BaseModel):
    """Request to refresh analytics."""
    video_id: Optional[str] = None  # Refresh specific video or all


class VideoAnalytics(BaseModel):
    """Analytics for a single video."""
    video_id: str
    youtube_id: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    watch_time_pct: float = 0
    ctr: float = 0
    subs_gained: int = 0
    score: float = 0


class AnalyticsSummary(BaseModel):
    """Dashboard analytics summary."""
    total_videos: int = 0
    total_views: int = 0
    avg_score: float = 0
    best_hook_style: Optional[str] = None
    recent_videos: List[Video] = []
    improvement_tip: Optional[str] = None


# ==================== Progress ====================

class ProgressUpdate(BaseModel):
    """SSE progress update message."""
    step: str
    progress: int  # 0-100
    message: str
    status: str = "running"  # running, complete, error
