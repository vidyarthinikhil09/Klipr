"""
Configuration settings for AutoShorts backend.
Uses pydantic-settings for environment variable management.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "AutoShorts API"
    debug: bool = False
    
    # CORS
    frontend_url: str = "http://localhost:5173"  # Vite default
    
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""  # For admin operations
    
    # Twitch API
    twitch_client_id: str = ""
    twitch_client_secret: str = ""
    
    # OpenRouter (LLM)
    openrouter_api_key: str = ""
    
    # Pexels (B-roll)
    pexels_api_key: str = ""
    
    # YouTube OAuth
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    
    # Groq (optional backup LLM)
    groq_api_key: Optional[str] = None
    
    # Storage paths
    temp_dir: str = "temp"
    output_dir: str = "output"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars like FLASK_*


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Creator roster configuration
CREATORS = {
    "tier1": [
        "IShowSpeed", "KaiCenat", "xQc", "MrBeast", "AdinRoss"
    ],
    "tier2": [
        "Tyler1", "Pokimane", "Ninja", "NICKMERCS", "Valkyrae",
        "Ludwig", "Mizkif", "HasanAbi", "Shroud", "Summit1g",
        "Sodapoppin", "Amouranth", "CohhCarnage", "TimTheTatman",
        "DrDisrespect", "Tfue", "Sykkuno"
    ],
    "tier3": [
        "QTCinderella", "Penguinz0", "JustaMinx", "ironmouse",
        "Lirik", "Asmongold"
    ]
}

# All creators flattened
ALL_CREATORS = CREATORS["tier1"] + CREATORS["tier2"] + CREATORS["tier3"]

# Twitch Game IDs for game-based clip discovery
GAMES = {
    "Valorant": "516575",
    "Fortnite": "33214",
    "Apex Legends": "511224",
    "Counter-Strike 2": "32399",
    "Minecraft": "27471",
    "GTA V": "32982",
    "League of Legends": "21779",
    "Call of Duty": "512710",
    "Just Chatting": "509658",
    "Overwatch 2": "515025"
}

# Niches - grouped creators by content type
NICHES = {
    "Rage & Reactions": {
        "emoji": "😤",
        "description": "Streamers known for intense reactions",
        "creators": ["IShowSpeed", "Tyler1", "xQc", "Asmongold", "DrDisrespect"]
    },
    "Gaming Pro": {
        "emoji": "🎯",
        "description": "Competitive and skilled gameplay",
        "creators": ["Shroud", "Ninja", "Tfue", "NICKMERCS", "Summit1g"]
    },
    "Just Vibes": {
        "emoji": "😎",
        "description": "Chill streams and hangouts",
        "creators": ["KaiCenat", "AdinRoss", "Ludwig", "Mizkif", "Sodapoppin"]
    },
    "Commentary & Politics": {
        "emoji": "🎙️",
        "description": "Hot takes and discussions",
        "creators": ["HasanAbi", "Penguinz0", "Lirik", "CohhCarnage"]
    },
    "Entertainment & IRL": {
        "emoji": "🎭",
        "description": "IRL content and entertainment",
        "creators": ["Pokimane", "Valkyrae", "QTCinderella", "JustaMinx", "Amouranth"]
    },
    "Anime & VTubers": {
        "emoji": "🌸",
        "description": "Anime fans and virtual streamers",
        "creators": ["ironmouse", "Sykkuno", "Valkyrae"]
    }
}

# OpenRouter free models for script generation
OPENROUTER_MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "google/gemma-7b-it:free",
    "nousresearch/nous-capybara-7b:free"
]

# Hook styles for self-learning metadata
HOOK_STYLES = [
    "shock",      # "You WON'T believe..."
    "question",   # "Did this streamer really...?"
    "emotional",  # "This made everyone cry..."
    "curiosity",  # "What happens next is insane"
    "hype",       # "THE MOST INSANE PLAY EVER"
    "controversy" # "This got them BANNED..."
]

# Edge-TTS voice options
TTS_VOICES = [
    "en-US-GuyNeural",      # Male, energetic
    "en-US-AriaNeural",     # Female, clear
    "en-US-ChristopherNeural",  # Male, deep
    "en-US-JennyNeural"     # Female, friendly
]
