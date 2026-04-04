"""
Supabase database client and utilities.
Handles all database operations for multi-user support.
"""
from functools import lru_cache
from typing import Optional
from supabase import create_client, Client
from .config import get_settings


@lru_cache()
def get_supabase() -> Client:
    """Get cached Supabase client."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_admin_supabase() -> Client:
    """Get Supabase client with service role (admin) key."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


class Database:
    """Database operations wrapper."""
    
    def __init__(self, user_id: Optional[str] = None, use_service_role: bool = False):
        # Use service role for server-side operations (bypasses RLS)
        if use_service_role:
            self.client = get_admin_supabase()
        else:
            self.client = get_supabase()
        self.user_id = user_id
    
    # ==================== YouTube Tokens ====================
    
    async def save_youtube_token(self, access_token: str, refresh_token: str, expires_at: str):
        """Save or update user's YouTube OAuth tokens."""
        if not self.user_id:
            raise ValueError("User ID required")
        
        from datetime import datetime
        
        # Use admin client to bypass RLS for server-side token storage
        admin_client = get_admin_supabase()
        
        # Check if token exists
        existing = admin_client.table("youtube_tokens").select("id").eq("user_id", self.user_id).execute()
        
        if existing.data:
            # Update existing
            admin_client.table("youtube_tokens").update({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at
            }).eq("user_id", self.user_id).execute()
        else:
            # Insert new
            admin_client.table("youtube_tokens").insert({
                "user_id": self.user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at
            }).execute()
    
    async def get_youtube_token(self) -> Optional[dict]:
        """Get user's YouTube OAuth tokens."""
        if not self.user_id:
            return None
        
        admin_client = get_admin_supabase()
        result = admin_client.table("youtube_tokens").select("*").eq(
            "user_id", self.user_id
        ).execute()
        
        return result.data[0] if result.data else None
    
    # ==================== Videos ====================
    
    async def save_video(self, video_data: dict) -> dict:
        """Save a generated video record."""
        video_data["user_id"] = self.user_id
        admin_client = get_admin_supabase()
        result = admin_client.table("videos").insert(video_data).execute()
        return result.data[0] if result.data else {}
    
    async def get_videos(self, limit: int = 20) -> list:
        """Get user's videos."""
        admin_client = get_admin_supabase()
        print(f"[DB] Getting videos for user_id: {self.user_id}")
        result = admin_client.table("videos").select("*").eq(
            "user_id", self.user_id
        ).order("created_at", desc=True).limit(limit).execute()
        print(f"[DB] Found {len(result.data) if result.data else 0} videos")
        return result.data or []
    
    async def update_video(self, video_id: str, updates: dict):
        """Update a video record."""
        admin_client = get_admin_supabase()
        admin_client.table("videos").update(updates).eq(
            "id", video_id
        ).eq("user_id", self.user_id).execute()
    
    async def get_video(self, video_id: str) -> Optional[dict]:
        """Get a single video by ID."""
        admin_client = get_admin_supabase()
        result = admin_client.table("videos").select("*").eq(
            "id", video_id
        ).eq("user_id", self.user_id).execute()
        return result.data[0] if result.data else None
    
    # ==================== Used Clips ====================
    
    async def is_clip_used(self, clip_id: str) -> bool:
        """Check if a clip has already been used by this user."""
        admin_client = get_admin_supabase()
        result = admin_client.table("used_clips").select("id").eq(
            "user_id", self.user_id
        ).eq("clip_id", clip_id).execute()
        return len(result.data) > 0
    
    async def mark_clip_used(self, clip_id: str, clip_url: str, creator: str):
        """Mark a clip as used."""
        admin_client = get_admin_supabase()
        admin_client.table("used_clips").insert({
            "user_id": self.user_id,
            "clip_id": clip_id,
            "clip_url": clip_url,
            "creator": creator
        }).execute()
    
    async def get_used_clips(self, limit: int = 100) -> list:
        """Get list of used clips."""
        admin_client = get_admin_supabase()
        result = admin_client.table("used_clips").select("clip_id").eq(
            "user_id", self.user_id
        ).order("used_at", desc=True).limit(limit).execute()
        return [r["clip_id"] for r in result.data] if result.data else []
    
    # ==================== Analytics ====================
    
    async def save_analytics_snapshot(self, video_id: str, analytics: dict):
        """Save an analytics snapshot for a video."""
        admin_client = get_admin_supabase()
        admin_client.table("analytics_history").insert({
            "user_id": self.user_id,
            "video_id": video_id,
            "views": analytics.get("views", 0),
            "likes": analytics.get("likes", 0),
            "watch_time_pct": analytics.get("watch_time_pct", 0),
            "ctr": analytics.get("ctr", 0),
            "score": analytics.get("score", 0)
        }).execute()
    
    async def get_analytics_summary(self) -> dict:
        """Get aggregated analytics for dashboard."""
        videos = await self.get_videos(limit=50)
        
        if not videos:
            return {
                "total_videos": 0,
                "total_views": 0,
                "avg_score": 0,
                "best_hook_style": None,
                "recent_videos": []
            }
        
        total_views = sum(v.get("views", 0) for v in videos)
        scores = [v.get("score", 0) for v in videos if v.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Find best performing hook style
        hook_scores = {}
        for v in videos:
            style = v.get("hook_style")
            if style:
                if style not in hook_scores:
                    hook_scores[style] = []
                hook_scores[style].append(v.get("score", 0))
        
        best_hook = None
        if hook_scores:
            best_hook = max(hook_scores.keys(), key=lambda k: sum(hook_scores[k]) / len(hook_scores[k]))
        
        return {
            "total_videos": len(videos),
            "total_views": total_views,
            "avg_score": round(avg_score, 1),
            "best_hook_style": best_hook,
            "recent_videos": videos[:10]
        }
