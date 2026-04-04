"""
Clips API routes - Discover and download Twitch clips.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio

from ..models.schemas import ClipDiscoveryRequest, ClipResponse, Clip
from ..auth.dependencies import get_current_user
from ..database import Database
from ..services.clip_finder import ClipFinder
from ..config import get_settings, ALL_CREATORS, GAMES, NICHES

router = APIRouter()


@router.get("/creators")
async def list_creators():
    """Get list of available creators."""
    from ..config import CREATORS
    return CREATORS


@router.get("/games")
async def list_games():
    """Get list of available games."""
    return GAMES


@router.get("/niches")
async def list_niches():
    """Get list of available niches with their creators."""
    return NICHES


@router.post("/discover", response_model=ClipResponse)
async def discover_clip(
    request: ClipDiscoveryRequest,
    user: dict = Depends(get_current_user)
):
    """
    Discover the best trending clip.
    
    - **mode**: 'creator', 'game', or 'niche'
    - **creator**: Specific creator name (optional, auto-selects if not provided)
    - **game**: Specific game name (optional)
    - **niche**: Specific niche name (optional)
    """
    settings = get_settings()
    db = Database(user.get("id"))
    
    # Get used clips to exclude
    used_clips = await db.get_used_clips()
    
    # Initialize clip finder
    finder = ClipFinder(
        client_id=settings.twitch_client_id,
        client_secret=settings.twitch_client_secret
    )
    
    try:
        if request.mode == "game" and request.game:
            if request.game not in GAMES:
                raise HTTPException(status_code=400, detail=f"Unknown game: {request.game}")
            
            clip_data = finder.get_best_clip_by_game(
                game_id=GAMES[request.game],
                exclude_ids=used_clips
            )
        elif request.mode == "niche" and request.niche:
            if request.niche not in NICHES:
                raise HTTPException(status_code=400, detail=f"Unknown niche: {request.niche}")
            
            # Get creators for this niche
            niche_creators = NICHES[request.niche]["creators"]
            clip_data = finder.get_best_clip(
                creators=niche_creators,
                exclude_ids=used_clips
            )
        else:
            # Creator mode
            creators = [request.creator] if request.creator else ALL_CREATORS
            clip_data = finder.get_best_clip(
                creators=creators,
                exclude_ids=used_clips
            )
        
        if not clip_data:
            return ClipResponse(
                success=False,
                message="No suitable clips found. Try a different creator or game."
            )
        
        clip = Clip(
            id=clip_data["id"],
            url=clip_data["url"],
            embed_url=clip_data.get("embed_url", ""),
            broadcaster_name=clip_data["broadcaster_name"],
            title=clip_data["title"],
            view_count=clip_data["view_count"],
            duration=clip_data.get("duration", 30),
            thumbnail_url=clip_data["thumbnail_url"],
            created_at=clip_data["created_at"],
            game_id=clip_data.get("game_id")
        )
        
        return ClipResponse(
            success=True,
            clip=clip,
            message=f"Found clip from {clip.broadcaster_name}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_clip(
    clip_url: str,
    user: dict = Depends(get_current_user)
):
    """
    Download a Twitch clip to local storage.
    Returns the local file path.
    """
    settings = get_settings()
    
    finder = ClipFinder(
        client_id=settings.twitch_client_id,
        client_secret=settings.twitch_client_secret
    )
    
    try:
        local_path = finder.download_clip(clip_url, output_dir=settings.temp_dir)
        
        if not local_path:
            raise HTTPException(status_code=500, detail="Failed to download clip")
        
        return {
            "success": True,
            "local_path": local_path,
            "message": "Clip downloaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-used")
async def mark_clip_used(
    clip_id: str,
    clip_url: str,
    creator: str,
    user: dict = Depends(get_current_user)
):
    """Mark a clip as used to prevent reuse."""
    db = Database(user.get("id"))
    await db.mark_clip_used(clip_id, clip_url, creator)
    return {"success": True}
