"""
ClipFinder Service - Twitch Clip Discovery and Download.
Adapted for FastAPI backend with constructor-injected credentials.
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
from typing import Optional, List, Set
import os


class ClipFinder:
    """Discovers and downloads trending Twitch clips."""
    
    TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
    TWITCH_API_URL = "https://api.twitch.tv/helix"
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize with Twitch credentials.
        
        Args:
            client_id: Twitch Client ID
            client_secret: Twitch Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.session_tried_clips: Set[str] = set()
    
    def authenticate(self) -> bool:
        """Get OAuth2 token from Twitch."""
        if not self.client_id or not self.client_secret:
            raise ValueError("Twitch credentials not provided")
        
        response = requests.post(self.TWITCH_AUTH_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        })
        
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            return True
        else:
            raise Exception(f"Twitch auth failed: {response.text}")
    
    def _get_headers(self) -> dict:
        """Get headers for Twitch API requests."""
        if not self.access_token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Client-Id": self.client_id
        }
    
    def get_broadcaster_id(self, username: str) -> Optional[str]:
        """Get broadcaster ID from username."""
        response = requests.get(
            f"{self.TWITCH_API_URL}/users",
            headers=self._get_headers(),
            params={"login": username}
        )
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data:
                return data[0]["id"]
        return None
    
    def get_clips(self, broadcaster_id: str, days: int = 1, limit: int = 20) -> list:
        """Get top clips for a broadcaster."""
        started_at = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
        params = {
            "broadcaster_id": broadcaster_id,
            "started_at": started_at,
            "first": limit
        }
        
        response = requests.get(
            f"{self.TWITCH_API_URL}/clips",
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    
    def get_clips_by_game(self, game_id: str, days: int = 7, limit: int = 50) -> list:
        """Get top clips for a specific game across ALL streamers."""
        started_at = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
        params = {
            "game_id": game_id,
            "started_at": started_at,
            "first": min(limit, 100)
        }
        
        response = requests.get(
            f"{self.TWITCH_API_URL}/clips",
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            clips = response.json().get("data", [])
            return clips
        return []
    
    def get_best_clip(
        self,
        creators: List[str],
        exclude_ids: List[str] = None
    ) -> Optional[dict]:
        """Find the best clip across specified creators."""
        if not self.access_token:
            self.authenticate()
        
        exclude_set = set(exclude_ids or [])
        all_clips = []
        
        for username in creators:
            broadcaster_id = self.get_broadcaster_id(username)
            if broadcaster_id:
                clips = self.get_clips(broadcaster_id, days=7, limit=20)
                for clip in clips:
                    clip["creator_username"] = username
                    all_clips.append(clip)
        
        # Filter out used/tried clips
        available_clips = [
            c for c in all_clips
            if c["id"] not in exclude_set
            and c["id"] not in self.session_tried_clips
        ]
        
        if not available_clips:
            return None
        
        # Sort by view count
        available_clips.sort(key=lambda x: x.get("view_count", 0), reverse=True)
        
        return available_clips[0]
    
    def get_best_clip_by_game(
        self,
        game_id: str,
        exclude_ids: List[str] = None
    ) -> Optional[dict]:
        """Find the best clip for a game."""
        if not self.access_token:
            self.authenticate()
        
        exclude_set = set(exclude_ids or [])
        clips = self.get_clips_by_game(game_id, days=7, limit=100)
        
        available_clips = [
            c for c in clips
            if c["id"] not in exclude_set
            and c["id"] not in self.session_tried_clips
        ]
        
        if not available_clips:
            return None
        
        available_clips.sort(key=lambda x: x.get("view_count", 0), reverse=True)
        
        return available_clips[0]
    
    def _get_clip_video_url(self, clip_id: str) -> str:
        """Get direct video URL using Twitch GQL API."""
        gql_query = """
        query ClipAccessToken($slug: ID!) {
            clip(slug: $slug) {
                playbackAccessToken(params: {platform: "web", playerType: "site"}) {
                    signature
                    value
                }
                videoQualities {
                    sourceURL
                    quality
                }
            }
        }
        """
        
        response = requests.post(
            "https://gql.twitch.tv/gql",
            json={
                "query": gql_query,
                "variables": {"slug": clip_id}
            },
            headers={
                "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",  # Public Twitch web client ID
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Twitch GQL API error: {response.status_code}")
        
        data = response.json()
        clip_data = data.get("data", {}).get("clip")
        
        if not clip_data:
            raise Exception(f"Clip not found: {clip_id}")
        
        qualities = clip_data.get("videoQualities", [])
        token_data = clip_data.get("playbackAccessToken", {})
        
        if not qualities:
            raise Exception(f"No video qualities found for clip {clip_id}")
        
        qualities.sort(key=lambda x: int(x.get("quality", "0")), reverse=True)
        base_url = qualities[0]["sourceURL"]
        
        sig = token_data.get("signature", "")
        tok = token_data.get("value", "")
        
        if sig and tok:
            import urllib.parse
            return f"{base_url}?sig={sig}&token={urllib.parse.quote(tok)}"
        
        return base_url
    
    def download_clip(self, clip_url: str, output_dir: str = "temp") -> Optional[str]:
        """
        Download a clip from its URL.
        Returns the path to the downloaded file or None if failed.
        """
        # Extract clip ID from URL
        if "twitch.tv" in clip_url:
            clip_id = clip_url.split("/")[-1].split("?")[0]
        else:
            clip_id = clip_url
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{clip_id}.mp4")
        
        # Check if already downloaded
        if os.path.exists(output_path):
            if self._validate_clip_audio(output_path):
                return output_path
            else:
                os.remove(output_path)
        
        try:
            video_url = self._get_clip_video_url(clip_id)
            
            response = requests.get(video_url, stream=True, timeout=120)
            if response.status_code != 200:
                raise Exception(f"Download failed: HTTP {response.status_code}")
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            
            if not os.path.exists(output_path):
                return None
            
            # Validate audio
            if not self._validate_clip_audio(output_path):
                self.session_tried_clips.add(clip_id)
                os.remove(output_path)
                return None
            
            return output_path
            
        except Exception as e:
            self.session_tried_clips.add(clip_id)
            print(f"Download error: {e}")
            return None
    
    def _validate_clip_audio(self, video_path: str) -> bool:
        """Check if video has actual audio (not silent/muted)."""
        try:
            from moviepy import VideoFileClip
            import numpy as np
            
            clip = VideoFileClip(video_path)
            
            if not clip.audio:
                clip.close()
                return False
            
            sample_duration = min(3.0, clip.audio.duration)
            audio_array = clip.audio.subclipped(0, sample_duration).to_soundarray(fps=22050)
            max_level = np.max(np.abs(audio_array))
            
            clip.close()
            
            return max_level > 0.01
            
        except Exception as e:
            print(f"Audio validation error: {e}")
            return True
