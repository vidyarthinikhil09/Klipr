"""
Analytics API routes - YouTube analytics and self-improvement.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import httpx

from ..models.schemas import AnalyticsRefreshRequest, AnalyticsSummary, VideoAnalytics
from ..auth.dependencies import get_current_user, require_youtube
from ..database import Database
from ..config import get_settings

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(user: dict = Depends(get_current_user)):
    """
    Get analytics summary for dashboard.
    Includes total views, avg score, best hook style, etc.
    """
    db = Database(user.get("id"))
    summary = await db.get_analytics_summary()
    
    # Add improvement tip based on data
    tip = _generate_improvement_tip(summary)
    
    return AnalyticsSummary(
        total_videos=summary.get("total_videos", 0),
        total_views=summary.get("total_views", 0),
        avg_score=summary.get("avg_score", 0),
        best_hook_style=summary.get("best_hook_style"),
        recent_videos=summary.get("recent_videos", []),
        improvement_tip=tip
    )


def _generate_improvement_tip(summary: dict) -> Optional[str]:
    """Generate a tip based on analytics data."""
    if summary.get("total_videos", 0) < 3:
        return "Upload at least 3 videos to start seeing performance insights!"
    
    best_hook = summary.get("best_hook_style")
    if best_hook:
        tips = {
            "shock": "Shocking hooks work well for you! Keep using surprising statements.",
            "question": "Question-based hooks engage your audience. Try more rhetorical questions!",
            "emotional": "Emotional hooks resonate with viewers. Lean into storytelling.",
            "curiosity": "Curiosity-driven titles perform well. Create more mystery!",
            "hype": "High-energy hype works for your channel. Keep the excitement up!",
            "controversy": "Controversial takes get clicks. But be careful not to overdo it."
        }
        return tips.get(best_hook, f"Your '{best_hook}' style performs best. Use it more!")
    
    return "Keep uploading to gather more data for AI optimization!"


@router.post("/refresh")
async def refresh_analytics(
    request: AnalyticsRefreshRequest = None,
    user: dict = Depends(require_youtube)
):
    """
    Refresh analytics from YouTube.
    Fetches latest views, likes, etc. for all uploaded videos.
    """
    settings = get_settings()
    db = Database(user.get("id"))
    
    # Get YouTube token
    youtube_token = user.get("youtube_token")
    if not youtube_token:
        raise HTTPException(status_code=403, detail="YouTube not connected")
    
    access_token = youtube_token.get("access_token")
    
    # Get videos to refresh
    videos = await db.get_videos(limit=50)
    uploaded_videos = [v for v in videos if v.get("youtube_id")]
    
    if not uploaded_videos:
        return {
            "success": True,
            "message": "No uploaded videos to refresh",
            "updated": 0
        }
    
    updated_count = 0
    
    for video in uploaded_videos:
        if request and request.video_id and video["id"] != request.video_id:
            continue
        
        try:
            stats = await _fetch_video_stats(access_token, video["youtube_id"])
            
            if stats:
                await db.update_video(video["id"], {
                    "views": stats.get("views", 0),
                    "likes": stats.get("likes", 0)
                })
                
                # Save analytics snapshot
                await db.save_analytics_snapshot(video["id"], stats)
                updated_count += 1
                
        except Exception as e:
            print(f"Failed to refresh {video['id']}: {e}")
    
    return {
        "success": True,
        "message": f"Refreshed {updated_count} videos",
        "updated": updated_count
    }


async def _fetch_video_stats(access_token: str, youtube_id: str) -> Optional[dict]:
    """
    Fetch video statistics from YouTube Data API.
    This is REAL-TIME data (unlike Analytics API which has 24-48hr delay).
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/youtube/v3/videos",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "id": youtube_id,
                "part": "statistics"
            }
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data.get("items"):
            return None
        
        stats = data["items"][0].get("statistics", {})
        
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0))
        }


@router.get("/video/{video_id}", response_model=VideoAnalytics)
async def get_video_analytics(
    video_id: str,
    user: dict = Depends(get_current_user)
):
    """Get analytics for a specific video."""
    db = Database(user.get("id"))
    video = await db.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoAnalytics(
        video_id=video_id,
        youtube_id=video.get("youtube_id"),
        views=video.get("views", 0),
        likes=video.get("likes", 0),
        watch_time_pct=video.get("watch_time_pct", 0),
        ctr=video.get("ctr", 0),
        subs_gained=video.get("subs_gained", 0),
        score=video.get("score", 0)
    )


@router.get("/feedback")
async def get_ai_feedback(user: dict = Depends(get_current_user)):
    """
    Get AI-generated feedback based on video performance.
    This is what gets injected into the LLM prompt for self-improvement.
    """
    db = Database(user.get("id"))
    summary = await db.get_analytics_summary()
    
    feedback_parts = []
    
    videos = summary.get("recent_videos", [])
    if len(videos) < 3:
        return {
            "has_feedback": False,
            "feedback": None,
            "message": "Need at least 3 videos for AI feedback"
        }
    
    # Analyze hook style performance
    hook_performance = {}
    for v in videos:
        style = v.get("hook_style")
        if style:
            if style not in hook_performance:
                hook_performance[style] = {"views": [], "scores": []}
            hook_performance[style]["views"].append(v.get("views", 0))
            hook_performance[style]["scores"].append(v.get("score", 0))
    
    if hook_performance:
        best_style = max(
            hook_performance.keys(),
            key=lambda k: sum(hook_performance[k]["scores"]) / len(hook_performance[k]["scores"])
        )
        worst_style = min(
            hook_performance.keys(),
            key=lambda k: sum(hook_performance[k]["scores"]) / len(hook_performance[k]["scores"])
        )
        
        if best_style != worst_style:
            feedback_parts.append(
                f"'{best_style}' hooks perform significantly better than '{worst_style}' hooks. "
                f"Prioritize {best_style} style."
            )
    
    # Analyze view trends
    if len(videos) >= 5:
        recent_3 = videos[:3]
        older_3 = videos[3:6]
        
        recent_avg = sum(v.get("views", 0) for v in recent_3) / 3
        older_avg = sum(v.get("views", 0) for v in older_3) / 3
        
        if recent_avg > older_avg * 1.2:
            feedback_parts.append("Your recent videos are trending up! Keep the current style.")
        elif recent_avg < older_avg * 0.8:
            feedback_parts.append(
                "Recent videos are underperforming. Try a different approach - "
                "consider more controversial hooks or emotional storytelling."
            )
    
    if feedback_parts:
        feedback = " ".join(feedback_parts)
        return {
            "has_feedback": True,
            "feedback": feedback,
            "hook_performance": hook_performance
        }
    
    return {
        "has_feedback": False,
        "feedback": None,
        "message": "Not enough variation in data for specific feedback"
    }
