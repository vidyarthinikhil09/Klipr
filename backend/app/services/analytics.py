"""
Analytics Service - YouTube Analytics and Self-Improvement.
Fetches real-time stats and generates feedback for AI optimization.
"""
import httpx
from typing import Optional, List
from datetime import datetime, timedelta


class AnalyticsService:
    """Handles YouTube analytics fetching and performance tracking."""
    
    def __init__(self, access_token: str):
        """Initialize with OAuth access token."""
        self.access_token = access_token
    
    async def get_video_stats(self, video_id: str) -> Optional[dict]:
        """Get real-time video statistics using YouTube Data API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "id": video_id,
                    "part": "statistics,snippet"
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("items"):
                return None
            
            item = data["items"][0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            
            return {
                "video_id": video_id,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt", "")
            }
    
    async def get_channel_videos(self, limit: int = 50) -> List[dict]:
        """Get list of channel videos."""
        async with httpx.AsyncClient() as client:
            # First get channel ID
            channel_response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "part": "contentDetails",
                    "mine": "true"
                }
            )
            
            if channel_response.status_code != 200:
                return []
            
            channel_data = channel_response.json()
            if not channel_data.get("items"):
                return []
            
            uploads_playlist = channel_data["items"][0].get(
                "contentDetails", {}
            ).get("relatedPlaylists", {}).get("uploads")
            
            if not uploads_playlist:
                return []
            
            # Get videos from uploads playlist
            videos_response = await client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "part": "snippet",
                    "playlistId": uploads_playlist,
                    "maxResults": limit
                }
            )
            
            if videos_response.status_code != 200:
                return []
            
            videos_data = videos_response.json()
            videos = []
            
            for item in videos_data.get("items", []):
                snippet = item.get("snippet", {})
                videos.append({
                    "video_id": snippet.get("resourceId", {}).get("videoId"),
                    "title": snippet.get("title"),
                    "published_at": snippet.get("publishedAt")
                })
            
            return videos
    
    def calculate_score(self, stats: dict, video_duration: float = 55) -> float:
        """
        Calculate performance score for a video.
        
        Formula: (views × 0.4) + (watch_time_pct × 0.3) + (CTR × 0.2) + (subs × 0.1)
        
        Since we don't have watch_time and CTR from basic API, we use a simplified formula:
        score = (views × 0.5) + (likes_ratio × 30) + (comments × 0.5)
        """
        views = stats.get("views", 0)
        likes = stats.get("likes", 0)
        comments = stats.get("comments", 0)
        
        # Likes ratio (likes per view)
        likes_ratio = (likes / views) if views > 0 else 0
        
        # Simplified score
        score = (
            (views * 0.5) +           # Views weight
            (likes_ratio * 30 * 100) +  # Engagement weight
            (comments * 0.5)           # Comments weight
        )
        
        return round(score, 2)
    
    def generate_feedback(self, videos: List[dict]) -> Optional[str]:
        """
        Generate AI feedback based on video performance.
        This gets injected into the LLM prompt for self-improvement.
        """
        if len(videos) < 3:
            return None
        
        feedback_parts = []
        
        # Analyze hook styles
        hook_performance = {}
        for v in videos:
            style = v.get("hook_style")
            score = v.get("score", 0)
            if style:
                if style not in hook_performance:
                    hook_performance[style] = []
                hook_performance[style].append(score)
        
        if hook_performance:
            best_style = max(
                hook_performance.keys(),
                key=lambda k: sum(hook_performance[k]) / len(hook_performance[k])
            )
            best_avg = sum(hook_performance[best_style]) / len(hook_performance[best_style])
            
            feedback_parts.append(
                f"'{best_style}' hooks perform best with avg score {best_avg:.1f}. "
                f"Prioritize {best_style} style hooks."
            )
        
        # Analyze view trends
        recent = videos[:3]
        older = videos[3:6] if len(videos) >= 6 else []
        
        if recent and older:
            recent_avg = sum(v.get("views", 0) for v in recent) / len(recent)
            older_avg = sum(v.get("views", 0) for v in older) / len(older)
            
            if recent_avg > older_avg * 1.2:
                feedback_parts.append("Recent videos trending UP! Keep current style.")
            elif recent_avg < older_avg * 0.8:
                feedback_parts.append(
                    "Recent performance down. Try more controversial/emotional hooks."
                )
        
        return " ".join(feedback_parts) if feedback_parts else None
