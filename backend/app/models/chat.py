from pydantic import BaseModel
from typing import List, Optional, Any
from app.models.memory import MemoryItem

class ChatMessage(BaseModel):
    id: Optional[int] = None
    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    recalled_memories: Optional[List[dict]] = []
    feedback_score: int = 0
    created_at: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    tone_override: Optional[dict] = None
    active_skill_id: Optional[int] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    recalled_memories: List[dict]
    learned_insights: List[dict] = []
    suggested_followups: List[str] = []

class FeedbackRequest(BaseModel):
    message_id: int
    score: int  # 1 for thumbs up, -1 for thumbs down
    correction_text: Optional[str] = None

class SessionItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
