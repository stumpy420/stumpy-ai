from pydantic import BaseModel, Field
from typing import List, Optional

class MemoryItem(BaseModel):
    id: Optional[int] = None
    category: str  # 'identity', 'preference', 'project', 'skill', 'habit', 'concept'
    topic: str
    content: str
    confidence: float = 1.0
    importance: float = 1.0
    access_count: int = 0
    is_pinned: bool = False
    source: str = "auto"  # 'auto', 'direct_teaching', 'correction', 'system'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TeachRequest(BaseModel):
    category: str = "preference"
    topic: str
    content: str
    is_pinned: bool = True

class MemoryQuery(BaseModel):
    query: str
    limit: int = 6
    category: Optional[str] = None

class KnowledgeGraphNode(BaseModel):
    id: str
    label: str
    category: str
    importance: float
    is_pinned: bool
    details: str

class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    weight: float = 1.0

class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]
    stats: dict
