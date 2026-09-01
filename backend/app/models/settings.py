from pydantic import BaseModel
from typing import Optional, Dict, Any

class SettingsModel(BaseModel):
    provider: str = "builtin"  # 'builtin', 'gemini', 'openai'
    gemini_api_key: Optional[str] = ""
    gemini_model: Optional[str] = "gemini-2.0-flash"
    openai_api_key: Optional[str] = ""
    openai_model: Optional[str] = "gpt-4o-mini"
    tone_conciseness: int = 50  # 0 to 100
    tone_formality: int = 40    # 0 to 100
    tone_style: str = "balanced" # 'socratic', 'direct', 'balanced', 'coach'
    auto_learning_enabled: bool = True
    memory_recall_limit: int = 6

class SystemStats(BaseModel):
    total_memories: int
    pinned_memories: int
    total_skills: int
    average_mastery: float
    total_notes: int
    total_chat_turns: int
    learned_insights_count: int
