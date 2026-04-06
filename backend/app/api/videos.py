"""
Videos API routes - Generate and manage videos.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, AsyncGenerator
import asyncio
import json
import os
import uuid
try:
    import psutil
except Exception:
    psutil = None

from ..models.schemas import (
    VideoGenerateRequest, VideoGenerateResponse, Video, 
    VideoMetadata, ProgressUpdate
)
from ..auth.dependencies import get_current_user
from ..database import Database
from ..config import get_settings

router = APIRouter()

# Store for SSE progress updates (in production, use Redis)
progress_store: dict = {}


async def progress_generator(task_id: str) -> AsyncGenerator[str, None]:
    """
    Server-Sent Events generator for progress updates.
    """
    while True:
        if task_id in progress_store:
            data = progress_store[task_id]
            yield f"data: {json.dumps(data)}\n\n"
            
            if data.get("status") in ["complete", "error"]:
                del progress_store[task_id]
                break
        
        await asyncio.sleep(0.5)


def update_progress(task_id: str, step: str, progress: int, message: str, status: str = "running"):
    """Update progress for a task."""
    progress_store[task_id] = {
        "step": step,
        "progress": progress,
        "message": message,
        "status": status
    }


def get_memory_mb() -> Optional[int]:
    """Return current process RSS in MB if psutil is available."""
    if psutil:
        try:
            return int(psutil.Process().memory_info().rss / (1024 * 1024))
        except Exception:
            return None
    return None


# Simple per-process render lock to avoid concurrent heavy renders in this process
render_lock = asyncio.Lock()


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: VideoGenerateRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Generate a video from a Twitch clip.
    
    Returns immediately with a task_id for progress tracking via SSE.
    """
    settings = get_settings()
    task_id = str(uuid.uuid4())
    
    # Initialize progress immediately so polling can see it
    update_progress(task_id, "starting", 5, "Initializing video generation...")
    
    # Start generation in background
    background_tasks.add_task(
        _generate_video_task,
        task_id=task_id,
        clip_url=request.clip_url,
        creator=request.creator,
        user_id=user.get("id"),
        settings=settings,
        title_override=request.title_override,
        description_override=request.description_override,
        caption_style=request.caption_style
    )
    
    return VideoGenerateResponse(
        success=True,
        message=f"Video generation started. Task ID: {task_id}",
        preview_url=f"/api/videos/progress/{task_id}"
    )


async def _generate_video_task(
    task_id: str,
    clip_url: str,
    creator: str,
    user_id: str,
    settings,
    title_override: Optional[str] = None,
    description_override: Optional[str] = None,
    caption_style: str = "mrbeast"
):
    """Background task to generate video."""
    import traceback
    
    from ..services.clip_finder import ClipFinder
    from ..services.transcriber import Transcriber
    from ..services.metadata_generator import MetadataGenerator
    from ..services.renderer import Renderer
    
    db = Database(user_id)
    
    try:
        # Step 1: Download clip
        update_progress(task_id, "download", 10, "Downloading clip...")
        print(f"[{task_id}] Starting download: {clip_url}")
        
        finder = ClipFinder(settings.twitch_client_id, settings.twitch_client_secret)
        clip_path = finder.download_clip(clip_url, output_dir=settings.temp_dir)
        
        if not clip_path:
            update_progress(task_id, "download", 0, "Failed to download clip - may be muted/DMCA", "error")
            print(f"[{task_id}] Download failed")
            return
        
        print(f"[{task_id}] Downloaded to: {clip_path}")
        
        # Step 2: Transcribe
        update_progress(task_id, "transcribe", 30, "Transcribing audio...")
        print(f"[{task_id}] Starting transcription")
        
        transcriber = Transcriber()
        transcript = transcriber.transcribe(clip_path)
        
        print(f"[{task_id}] Transcription complete: {len(transcript.get('words', []))} words")
        
        # Step 3: Generate metadata
        update_progress(task_id, "metadata", 50, "Generating AI metadata...")
        print(f"[{task_id}] Generating metadata")
        
        meta_gen = MetadataGenerator(settings.openrouter_api_key)
        
        # Get analytics feedback for self-improvement
        feedback = await _get_analytics_feedback(db)
        
        metadata = meta_gen.generate(
            transcript=transcript,
            creator=creator,
            feedback=feedback
        )
        
        print(f"[{task_id}] Metadata: {metadata.get('title', 'N/A')}")
        
        # Override if provided
        if title_override:
            metadata["title"] = title_override
        if description_override:
            metadata["description"] = description_override
        
        # Step 4: Render video (acquire per-process render lock)
        update_progress(task_id, "render", 70, "Waiting for render slot...")
        print(f"[{task_id}] Queueing render with style: {caption_style}")

        output_filename = f"short_{task_id[:8]}.mp4"
        output_path = os.path.join(settings.output_dir, output_filename)

        renderer = Renderer(caption_style=caption_style)
        # Lower bitrate for Render environments to reduce peak memory
        renderer.bitrate = getattr(renderer, "bitrate", "4M") or "4M"

        try:
            # Wait for lock to be free, polling with progress updates
            wait_seconds = 0
            while render_lock.locked():
                wait_seconds += 1
                update_progress(task_id, "render", 72, f"Renderer busy; waiting {wait_seconds}s...")
                mem = get_memory_mb()
                if mem:
                    print(f"[{task_id}] Waiting for renderer - memory usage: {mem} MB")
                await asyncio.sleep(1)

            async with render_lock:
                update_progress(task_id, "render", 75, "Rendering video with captions...")
                mem_before = get_memory_mb()
                if mem_before:
                    print(f"[{task_id}] Memory before render: {mem_before} MB")

                loop = asyncio.get_running_loop()
                # Run blocking render in threadpool to avoid blocking the event loop
                await loop.run_in_executor(
                    None,
                    lambda: renderer.render(
                        clip_path=clip_path,
                        transcript=transcript,
                        output_path=output_path,
                        progress_callback=lambda p: update_progress(task_id, "render", 75 + int(p * 0.20), f"Rendering: {int(p)}%")
                    )
                )

                mem_after = get_memory_mb()
                if mem_after:
                    print(f"[{task_id}] Memory after render: {mem_after} MB")

        except Exception as e:
            raise
        
        print(f"[{task_id}] Render complete: {output_path}")
        
        # Step 5: Save to database
        update_progress(task_id, "save", 98, "Saving video...")
        
        video_data = {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata.get("tags", []),
            "creator": creator,
            "clip_url": clip_url,
            "hook_style": metadata.get("hook_style"),
            "model_used": metadata.get("model_used"),
            "local_path": output_path,
            "status": "draft"
        }
        
        saved_video = await db.save_video(video_data)
        print(f"[{task_id}] Saved to DB: {saved_video.get('id', 'N/A')}")
        
        # Mark clip as used
        clip_id = clip_url.split("/")[-1] if "/" in clip_url else clip_url
        await db.mark_clip_used(clip_id, clip_url, creator)
        
        # Complete
        update_progress(task_id, "complete", 100, "Video ready!", "complete")
        progress_store[task_id]["video"] = saved_video
        print(f"[{task_id}] ✅ Complete!")
        
    except Exception as e:
        error_msg = str(e)
        print(f"[{task_id}] ❌ ERROR: {error_msg}")
        print(traceback.format_exc())
        update_progress(task_id, "error", 0, error_msg, "error")


async def _get_analytics_feedback(db: Database) -> Optional[str]:
    """Get analytics feedback for self-improvement."""
    try:
        summary = await db.get_analytics_summary()
        
        if summary["total_videos"] < 3:
            return None
        
        feedback_parts = []
        
        if summary["best_hook_style"]:
            feedback_parts.append(f"Your best performing hook style is '{summary['best_hook_style']}'.")
        
        if summary["avg_score"] > 0:
            feedback_parts.append(f"Your average video score is {summary['avg_score']}.")
        
        return " ".join(feedback_parts) if feedback_parts else None
        
    except Exception:
        return None


@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Server-Sent Events endpoint for real-time progress updates.
    """
    return StreamingResponse(
        progress_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    Simple polling endpoint for progress (alternative to SSE).
    Returns current progress state.
    """
    if task_id in progress_store:
        data = progress_store[task_id]
        print(f"[Status] Task {task_id}: {data.get('step')} - {data.get('progress')}%")
        return data
    # Return "pending" instead of error - task may not have started yet
    return {"step": "pending", "progress": 0, "message": "Waiting for task to start...", "status": "running"}


@router.get("/")
async def list_videos(
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """Get user's generated videos."""
    db = Database(user.get("id"))
    videos = await db.get_videos(limit=limit)
    return {"videos": videos}


@router.get("/{video_id}")
async def get_video(
    video_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific video by ID."""
    db = Database(user.get("id"))
    video = await db.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video


@router.patch("/{video_id}")
async def update_video_metadata(
    video_id: str,
    updates: dict,
    user: dict = Depends(get_current_user)
):
    """Update video metadata (title, description, tags)."""
    db = Database(user.get("id"))
    video = await db.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Only allow updating certain fields
    allowed_fields = {"title", "description", "tags"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    await db.update_video(video_id, filtered_updates)
    
    # Return updated video
    updated_video = await db.get_video(video_id)
    return updated_video


@router.get("/{video_id}/preview")
async def preview_video(
    video_id: str,
    user: dict = Depends(get_current_user)
):
    """Stream video file for preview."""
    db = Database(user.get("id"))
    video = await db.get_video(video_id)
    
    if not video or not video.get("local_path"):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video["local_path"],
        media_type="video/mp4",
        filename=f"preview_{video_id[:8]}.mp4"
    )


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a video (draft only, not uploaded)."""
    print(f"[Delete] Attempting to delete video {video_id} for user {user.get('id')}")
    db = Database(user.get("id"))
    video = await db.get_video(video_id)
    
    if not video:
        print(f"[Delete] Video {video_id} not found for user {user.get('id')}")
        raise HTTPException(status_code=404, detail="Video not found")
    
    print(f"[Delete] Found video: {video.get('title')}, status: {video.get('status')}")
    
    if video.get("status") == "uploaded":
        raise HTTPException(status_code=400, detail="Cannot delete uploaded videos")
    
    # Delete local file
    if video.get("local_path") and os.path.exists(video["local_path"]):
        try:
            os.remove(video["local_path"])
            print(f"[Delete] Removed local file: {video['local_path']}")
        except Exception as e:
            print(f"Warning: Could not delete file: {e}")
    
    # Delete from database using admin client to bypass RLS
    from ..database import get_admin_supabase
    admin_client = get_admin_supabase()
    result = admin_client.table("videos").delete().eq("id", video_id).eq("user_id", user.get("id")).execute()
    print(f"[Delete] Delete result: {result}")
    
    return {"success": True, "message": "Video deleted"}


@router.delete("/admin/cleanup-all")
async def cleanup_all_videos(user: dict = Depends(get_current_user)):
    """
    ADMIN: Delete all draft videos for current user.
    Use this to clean up stuck/orphan videos.
    """
    from ..database import get_admin_supabase
    admin_client = get_admin_supabase()
    
    # Get all videos for this user
    result = admin_client.table("videos").select("*").eq("user_id", user.get("id")).execute()
    
    deleted_count = 0
    for video in result.data or []:
        if video.get("status") != "uploaded":
            # Delete local file if exists
            if video.get("local_path"):
                try:
                    import os
                    if os.path.exists(video["local_path"]):
                        os.remove(video["local_path"])
                except Exception:
                    pass
            
            # Delete from DB
            admin_client.table("videos").delete().eq("id", video["id"]).execute()
            deleted_count += 1
    
    return {"success": True, "deleted": deleted_count, "message": f"Cleaned up {deleted_count} draft videos"}


@router.get("/renderer/status")
async def get_renderer_status():
    """
    Get renderer capabilities and status.
    Reports whether pycaps is available and any errors.
    """
    from ..services.renderer import PYCAPS_AVAILABLE, PYCAPS_ERROR
    
    return {
        "pycaps_available": PYCAPS_AVAILABLE,
        "pycaps_error": PYCAPS_ERROR,
        "renderer": "pycaps" if PYCAPS_AVAILABLE else "moviepy",
        "caption_styles": ["mrbeast", "hormozi", "tiktok", "karaoke", "minimalist", "classic"]
    }


@router.get("/debug/all-videos")
async def debug_all_videos(user: dict = Depends(get_current_user)):
    """
    DEBUG: See all videos in DB and their user_ids.
    Helps diagnose user isolation issues.
    """
    from ..database import get_admin_supabase
    admin_client = get_admin_supabase()
    
    # Get ALL videos (not filtered by user)
    result = admin_client.table("videos").select("id, user_id, title, status, created_at").order("created_at", desc=True).limit(20).execute()
    
    current_user_id = user.get("id")
    
    videos_info = []
    for v in result.data or []:
        videos_info.append({
            "id": v["id"],
            "user_id": v.get("user_id"),
            "belongs_to_current_user": v.get("user_id") == current_user_id,
            "title": v.get("title", "")[:50],
            "status": v.get("status")
        })
    
    return {
        "current_user_id": current_user_id,
        "total_videos_in_db": len(result.data or []),
        "videos": videos_info
    }
