import os
from pathlib import Path

# Base directories
# When deployed on Railway, __file__ is inside backend/app/
# STATIC_DIR needs to resolve to the frontend/ folder at project root
BASE_DIR = Path(__file__).resolve().parent.parent  # = stumpy-ai/backend/
PROJECT_ROOT = BASE_DIR.parent                      # = stumpy-ai/

# On Railway, use /data as a persistent volume or fallback to local
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "stumpy.db"
STATIC_DIR = PROJECT_ROOT / "frontend"

# Default Persona Settings
DEFAULT_SETTINGS = {
    "provider": "builtin",  # 'builtin', 'gemini', 'openai'
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "gemini_model": "gemini-2.0-flash",
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_model": "gpt-4o-mini",
    "tone_conciseness": 50,   # 0: very detailed, 100: very concise
    "tone_formality": 40,     # 0: playful/casual, 100: formal/academic
    "tone_style": "balanced", # 'socratic', 'direct', 'balanced', 'coach'
    "auto_learning_enabled": True,
    "memory_recall_limit": 6
}
