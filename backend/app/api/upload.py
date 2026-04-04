"""
Upload API routes - YouTube upload functionality.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import httpx

from ..models.schemas import UploadRequest, UploadResponse
from ..auth.dependencies import get_current_user, require_youtube
from ..database import Database
from ..config import get_settings

router = APIRouter()


@router.post("/youtube", response_model=UploadResponse)
async def upload_to_youtube(
    request: UploadRequest,
    user: dict = Depends(require_youtube)
):
    """
    Upload a generated video to YouTube.
    
    Requires YouTube account to be connected.
    """
    print(f"[Upload] Starting upload for user {user.get('id')}")
    settings = get_settings()
    db = Database(user.get("id"))
    
    # Get video from database
    video = await db.get_video(request.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    print(f"[Upload] Video found: {video.get('title')}")
    
    if video.get("status") == "uploaded":
        raise HTTPException(status_code=400, detail="Video already uploaded")
    
    if not video.get("local_path"):
        raise HTTPException(status_code=400, detail="Video file not found")
    
    # Get YouTube token
    youtube_token = user.get("youtube_token")
    print(f"[Upload] Token present: {youtube_token is not None}")
    if youtube_token:
        print(f"[Upload] Token has access_token: {'access_token' in youtube_token}")
        print(f"[Upload] Token has refresh_token: {'refresh_token' in youtube_token}")
    
    if not youtube_token:
        raise HTTPException(status_code=403, detail="YouTube not connected")
    
    # Check if token needs refresh
    access_token = await _ensure_valid_token(youtube_token, settings, db)
    print(f"[Upload] Got access token: {access_token[:20] if access_token else 'None'}...")
    
    # Prepare metadata
    title = request.title or video.get("title", "Epic Gaming Moment")
    description = request.description or video.get("description", "")
    tags = request.tags or video.get("tags", [])
    
    # Upload to YouTube
    try:
        youtube_id = await _upload_video(
            access_token=access_token,
            file_path=video["local_path"],
            title=title,
            description=description,
            tags=tags
        )
        
        if not youtube_id:
            raise HTTPException(status_code=500, detail="Upload failed")
        
        # Update video record
        await db.update_video(request.video_id, {
            "youtube_id": youtube_id,
            "status": "uploaded",
            "title": title,
            "description": description,
            "tags": tags
        })
        
        return UploadResponse(
            success=True,
            youtube_id=youtube_id,
            youtube_url=f"https://youtube.com/shorts/{youtube_id}",
            message="Video uploaded successfully!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def _ensure_valid_token(token: dict, settings, db: Database) -> str:
    """Refresh token if expired."""
    from datetime import datetime, timezone
    
    print(f"[Token] Checking token validity...")
    print(f"[Token] Token keys: {list(token.keys())}")
    
    expires_at = token.get("expires_at")
    if expires_at:
        try:
            # Handle various datetime formats
            if isinstance(expires_at, str):
                if expires_at.endswith('Z'):
                    expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                elif '+' in expires_at or expires_at.endswith('00'):
                    expiry = datetime.fromisoformat(expires_at)
                else:
                    expiry = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
            else:
                expiry = expires_at
            
            now = datetime.now(timezone.utc)
            print(f"[Token] Expires at: {expiry}, Now: {now}")
            
            if now >= expiry:
                print(f"[Token] Token expired, refreshing...")
                return await _refresh_token(token, settings, db)
            else:
                print(f"[Token] Token still valid")
        except Exception as e:
            print(f"[Token] Error checking expiry: {e}, attempting refresh anyway")
            return await _refresh_token(token, settings, db)
    else:
        print(f"[Token] No expires_at found, using token as-is")
    
    return token.get("access_token")


async def _refresh_token(token: dict, settings, db: Database) -> str:
    """Refresh YouTube OAuth token."""
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        print("[Token] ERROR: No refresh token available!")
        raise HTTPException(status_code=401, detail="No refresh token available. Please reconnect YouTube.")
    
    print(f"[Token] Refreshing with refresh_token: {refresh_token[:20]}...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.youtube_client_id,
                "client_secret": settings.youtube_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
    
    print(f"[Token] Refresh response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"[Token] Refresh failed: {response.text}")
        raise HTTPException(status_code=401, detail=f"Failed to refresh token: {response.text}. Please reconnect YouTube.")
    
    tokens = response.json()
    print(f"[Token] Got new access token: {tokens.get('access_token', '')[:20]}...")
    
    from datetime import datetime, timedelta, timezone
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    
    await db.save_youtube_token(
        access_token=tokens.get("access_token"),
        refresh_token=refresh_token,  # Keep original refresh token
        expires_at=expires_at.isoformat()
    )
    
    return tokens.get("access_token")


async def _upload_video(
    access_token: str,
    file_path: str,
    title: str,
    description: str,
    tags: list
) -> Optional[str]:
    """
    Upload video to YouTube using resumable upload.
    Returns YouTube video ID.
    """
    import os
    
    # Step 1: Initialize resumable upload
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "snippet": {
            "title": title[:100],  # YouTube limit
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": "20"  # Gaming
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False
        }
    }
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Initialize upload
        init_response = await client.post(
            "https://www.googleapis.com/upload/youtube/v3/videos"
            "?uploadType=resumable&part=snippet,status",
            headers=headers,
            json=metadata
        )
        
        if init_response.status_code != 200:
            raise Exception(f"Upload init failed: {init_response.text}")
        
        upload_url = init_response.headers.get("Location")
        if not upload_url:
            raise Exception("No upload URL returned")
        
        # Upload file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        upload_response = await client.put(
            upload_url,
            content=file_content,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size)
            }
        )
        
        if upload_response.status_code in [200, 201]:
            result = upload_response.json()
            return result.get("id")
        else:
            raise Exception(f"Upload failed: {upload_response.text}")


@router.get("/youtube/quota")
async def get_youtube_quota(user: dict = Depends(require_youtube)):
    """
    Get remaining YouTube API quota (approximate).
    YouTube gives 10,000 units/day, upload costs ~1,600 units.
    """
    # Note: YouTube doesn't have a direct quota API
    # This returns an estimate based on uploads today
    db = Database(user.get("id"))
    
    from datetime import datetime, timedelta
    videos = await db.get_videos(limit=100)
    
    # Count uploads in last 24 hours
    now = datetime.utcnow()
    today_uploads = sum(
        1 for v in videos
        if v.get("status") == "uploaded"
        and v.get("created_at")
        and (now - datetime.fromisoformat(v["created_at"].replace("Z", "+00:00"))) < timedelta(days=1)
    )
    
    estimated_used = today_uploads * 1600
    estimated_remaining = max(0, 10000 - estimated_used)
    
    return {
        "uploads_today": today_uploads,
        "estimated_used": estimated_used,
        "estimated_remaining": estimated_remaining,
        "max_daily": 10000,
        "cost_per_upload": 1600,
        "uploads_available": estimated_remaining // 1600
    }
