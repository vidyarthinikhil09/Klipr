"""
Authentication routes for Supabase Auth + YouTube OAuth.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
import httpx

from ..config import get_settings
from ..database import Database
from .dependencies import get_current_user

router = APIRouter()


@router.get("/login")
async def login_redirect():
    """
    Redirect to Supabase Auth login page.
    Frontend should use Supabase JS client directly, but this provides a fallback.
    """
    settings = get_settings()
    return {
        "message": "Use Supabase Auth in frontend",
        "supabase_url": settings.supabase_url
    }


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "has_youtube_token": False  # Will check database
    }


@router.get("/youtube/connect")
async def youtube_oauth_start(request: Request, user: dict = Depends(get_current_user)):
    """
    Start YouTube OAuth flow.
    Returns URL for user to authorize their YouTube account.
    """
    settings = get_settings()
    
    # Build OAuth URL
    redirect_uri = str(request.base_url) + "api/auth/youtube/callback"
    
    oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.youtube_client_id}"
        "&response_type=code"
        f"&redirect_uri={redirect_uri}"
        "&scope=https://www.googleapis.com/auth/youtube.upload "
        "https://www.googleapis.com/auth/youtube.readonly "
        "https://www.googleapis.com/auth/yt-analytics.readonly"
        "&access_type=offline"
        "&prompt=consent"
        f"&state={user.get('id')}"  # Pass user ID in state
    )
    
    return {"oauth_url": oauth_url}


@router.get("/youtube/callback")
async def youtube_oauth_callback(code: str, state: str, request: Request):
    """
    Handle YouTube OAuth callback.
    Exchange code for tokens and store in database.
    """
    settings = get_settings()
    redirect_uri = str(request.base_url) + "api/auth/youtube/callback"
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.youtube_client_id,
                "client_secret": settings.youtube_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")
    
    tokens = response.json()
    
    # Store tokens in database for this user
    user_id = state  # User ID passed in state parameter
    db = Database(user_id)
    
    from datetime import datetime, timedelta
    expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    
    await db.save_youtube_token(
        access_token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token", ""),
        expires_at=expires_at.isoformat()
    )
    
    # Redirect to frontend success page
    frontend_url = settings.frontend_url
    return RedirectResponse(url=f"{frontend_url}/auth/youtube/success")


@router.get("/youtube/status")
async def youtube_connection_status(user: dict = Depends(get_current_user)):
    """Check if user has connected their YouTube account."""
    db = Database(user.get("id"))
    token = await db.get_youtube_token()
    
    return {
        "connected": token is not None,
        "expires_at": token.get("expires_at") if token else None
    }


@router.delete("/youtube/disconnect")
async def youtube_disconnect(user: dict = Depends(get_current_user)):
    """Disconnect YouTube account (delete tokens)."""
    from ..database import get_supabase
    
    client = get_supabase()
    client.table("youtube_tokens").delete().eq(
        "user_id", user.get("id")
    ).execute()
    
    return {"success": True, "message": "YouTube disconnected"}
