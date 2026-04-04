"""
MetadataGenerator Service - Self-Healing AI Metadata Generation.
Uses OpenRouter free models and learns from YouTube Analytics.
"""
import json
import random
import requests
from datetime import datetime
from typing import Optional, List


class MetadataGenerator:
    """
    Generates optimized YouTube metadata using AI.
    Self-improves based on video performance analytics.
    """
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    HOOK_STYLES = ["shock", "question", "emotional", "curiosity", "hype", "controversy"]
    
    OPENROUTER_MODELS = [
        "qwen/qwen3.6-plus:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "google/gemini-2.5-flash:free",
        "meta-llama/llama-4-scout:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
    ]
    
    def __init__(self, api_key: str):
        """Initialize with OpenRouter API key."""
        self.api_key = api_key
        self.style_performance = self._get_default_performance()
    
    def _get_default_performance(self) -> dict:
        """Return default performance tracking structure."""
        return {
            "hook_styles": {style: {"uses": 0, "total_score": 0, "avg_score": 0} for style in self.HOOK_STYLES},
            "emoji_usage": {"with_emoji": {"uses": 0, "total_score": 0}, "without_emoji": {"uses": 0, "total_score": 0}},
            "best_performing": {
                "hook_style": "shock",
                "use_emoji": True,
            }
        }
    
    def update_performance_from_feedback(self, feedback: str):
        """Update preferences based on analytics feedback."""
        if not feedback:
            return
        
        # Parse feedback to update best performing style
        for style in self.HOOK_STYLES:
            if style in feedback.lower():
                self.style_performance["best_performing"]["hook_style"] = style
                break
    
    def _select_model(self) -> str:
        """Select an OpenRouter model."""
        return random.choice(self.OPENROUTER_MODELS)
    
    def _call_openrouter(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Call OpenRouter API with the given prompts. Tries multiple models on failure."""
        if not self.api_key:
            print("[MetadataGenerator] No OpenRouter API key configured - using fallback")
            return None
        
        # Try each model until one works
        models_to_try = self.OPENROUTER_MODELS.copy()
        random.shuffle(models_to_try)
        
        for model in models_to_try:
            print(f"[MetadataGenerator] Trying OpenRouter model: {model}")
            
            try:
                response = requests.post(
                    self.OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/autoshorts-bot",
                        "X-Title": "AutoShorts Bot"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.8
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(f"[MetadataGenerator] ✅ OpenRouter success with {model}! Response length: {len(content)}")
                    return content
                else:
                    print(f"[MetadataGenerator] Model {model} failed: {response.status_code}")
                    continue  # Try next model
                    
            except Exception as e:
                print(f"[MetadataGenerator] Model {model} exception: {e}")
                continue  # Try next model
        
        print("[MetadataGenerator] All OpenRouter models failed - using fallback")
        return None
    
    def _parse_metadata_response(self, response: str) -> dict:
        """Parse the LLM response into structured metadata."""
        metadata = {
            "title": "",
            "description": "",
            "tags": [],
            "hook_style": "unknown",
            "has_emoji": False
        }
        
        if not response:
            return metadata
        
        lines = response.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower = line.lower()
            
            if lower.startswith("title:") or lower.startswith("**title"):
                value = line.split(":", 1)[-1].strip().strip("*").strip('"').strip()
                if value:
                    metadata["title"] = value[:100]
            elif lower.startswith("description:") or lower.startswith("**description"):
                value = line.split(":", 1)[-1].strip().strip("*").strip()
                if value:
                    metadata["description"] = value
            elif lower.startswith("tags:") or lower.startswith("**tags"):
                value = line.split(":", 1)[-1].strip().strip("*").strip()
                if value:
                    tags = [t.strip().strip("#") for t in value.split(",")]
                    metadata["tags"] = [t for t in tags if t][:15]
            elif lower.startswith("hook_style:") or lower.startswith("**hook"):
                value = line.split(":", 1)[-1].strip().strip("*").lower()
                for style in self.HOOK_STYLES:
                    if style in value:
                        metadata["hook_style"] = style
                        break
        
        metadata["title"] = metadata["title"].strip()[:100]
        metadata["description"] = metadata["description"].strip()[:500]
        metadata["has_emoji"] = any(ord(c) > 127 for c in metadata["title"])
        
        return metadata
    
    def generate(
        self,
        transcript: dict,
        creator: str,
        game: str = None,
        feedback: str = None
    ) -> dict:
        """
        Generate optimized metadata for a clip.
        
        Args:
            transcript: Dict with text and words from transcription
            creator: Creator/streamer name
            game: Game name (optional)
            feedback: Analytics feedback for self-improvement (optional)
        
        Returns:
            Dict with title, description, tags, hook_style, model_used
        """
        if feedback:
            self.update_performance_from_feedback(feedback)
        
        best_hook = self.style_performance["best_performing"].get("hook_style", "shock")
        use_emoji = self.style_performance["best_performing"].get("use_emoji", True)
        
        clip_text = transcript.get("text", "")[:500]
        game_name = game or "Gaming"
        
        system_prompt = """You are a viral YouTube Shorts metadata expert. Create titles, descriptions, and tags that maximize views.

Rules:
- Titles must be under 60 characters (shorter is better for Shorts)
- Titles should create curiosity, shock, or emotion
- Description should include hashtags and a call-to-action
- Tags should be specific and trending

Always respond in this exact format:
TITLE: [your title here]
DESCRIPTION: [your description here]
TAGS: [comma-separated tags]
HOOK_STYLE: [shock/question/emotional/curiosity/hype/controversy]"""

        user_prompt = f"""Create viral YouTube Shorts metadata for this clip:

CLIP TRANSCRIPT: "{clip_text[:300]}..."

CREATOR: {creator}
GAME: {game_name}

PERFORMANCE INSIGHTS:
{feedback or "No data yet. Use viral, attention-grabbing style."}

OPTIMIZATION:
- Preferred hook style: {best_hook.upper()}
- Use emojis: {"YES" if use_emoji else "NO"}

Generate metadata that will go VIRAL!"""

        response = self._call_openrouter(user_prompt, system_prompt)
        model_used = self._select_model()
        
        if response:
            metadata = self._parse_metadata_response(response)
            metadata["model_used"] = model_used
        else:
            metadata = self._generate_fallback_metadata(creator, game_name, clip_text)
        
        metadata["creator"] = creator
        metadata["game"] = game_name
        
        return metadata
    
    def _generate_fallback_metadata(self, creator: str, game: str, text: str) -> dict:
        """Generate basic metadata when AI is unavailable."""
        hooks = [
            f"🔥 {creator} JUST DID THIS in {game}",
            f"😱 {creator}'s INSANE {game} moment",
            f"💀 This {game} clip is UNREAL",
            f"🎮 {creator} can't believe this happened",
        ]
        
        title = random.choice(hooks)[:60]
        
        description = f"""🎬 Epic {game} moment from {creator}!

👤 Streamer: {creator}
🎮 Game: {game}

#Shorts #Gaming #{game.replace(' ', '')} #{creator.replace(' ', '')} #Viral"""

        tags = [
            "shorts", "gaming", "twitch", "viral", "clips",
            game.lower().replace(" ", ""), creator.lower().replace(" ", ""),
            "funny", "epic", "moments"
        ]
        
        return {
            "title": title,
            "description": description,
            "tags": tags,
            "hook_style": "hype",
            "has_emoji": True,
            "model_used": "fallback"
        }
