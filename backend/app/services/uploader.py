"""
YouTube Uploader Service - Handles video uploads to YouTube.
Uses OAuth tokens stored per-user in database.
"""
import httpx
import os
from typing import Optional


class YouTubeUploader:
    """Handles YouTube video uploads."""
    
    def __init__(self, access_token: str):
        """Initialize with OAuth access token."""
        self.access_token = access_token
    
    async def upload(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: list,
        privacy: str = "public"
    ) -> Optional[str]:
        """
        Upload video to YouTube.
        
        Args:
            file_path: Path to video file
            title: Video title (max 100 chars)
            description: Video description
            tags: List of tags
            privacy: public, private, or unlisted
        
        Returns:
            YouTube video ID if successful, None otherwise
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": "20"  # Gaming
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
                "madeForKids": False
            }
        }
        
        file_size = os.path.getsize(file_path)
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Initialize resumable upload
            init_response = await client.post(
                "https://www.googleapis.com/upload/youtube/v3/videos"
                "?uploadType=resumable&part=snippet,status",
                headers=headers,
                json=metadata
            )
            
            if init_response.status_code != 200:
                print(f"Upload init failed: {init_response.text}")
                return None
            
            upload_url = init_response.headers.get("Location")
            if not upload_url:
                return None
            
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
                print(f"Upload failed: {upload_response.text}")
                return None
    
    async def get_video_stats(self, video_id: str) -> Optional[dict]:
        """Get real-time statistics for a video."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "id": video_id,
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
