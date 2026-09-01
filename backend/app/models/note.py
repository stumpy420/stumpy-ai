from pydantic import BaseModel
from typing import List, Optional

class KnowledgeNoteItem(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    tags: str = ""
    category: str = "general"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class KnowledgeNoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[str] = ""
    category: Optional[str] = "general"
