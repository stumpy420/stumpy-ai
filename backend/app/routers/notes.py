from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.models.note import KnowledgeNoteItem, KnowledgeNoteCreate
from app.models.user import UserResponse
from app.services.note_service import NoteService
from app.services.memory_engine import MemoryEngine
from app.services.auth_service import get_current_user
from app.services.tier_service import TierService

router = APIRouter(prefix="/api/notes", tags=["Knowledge Notes"])

@router.get("", response_model=List[KnowledgeNoteItem])
def list_notes(search: Optional[str] = None, tag: Optional[str] = None, user: UserResponse = Depends(get_current_user)):
    return NoteService.get_all_notes(search=search, tag=tag, user_id=user.id)

@router.post("", response_model=KnowledgeNoteItem)
def create_note(data: KnowledgeNoteCreate, user: UserResponse = Depends(get_current_user)):
    # Check Free tier note quota
    TierService.check_note_quota(user)

    note = NoteService.create_note(data, user_id=user.id)
    # Also index into memory store if memory quota allows
    if user.tier == "pro" or user.memories_count < user.memory_limit:
        MemoryEngine.add_memory(
            category="concept",
            topic=f"note_{data.title.lower().replace(' ', '_')[:30]}",
            content=f"Vault Note [{data.title}]: {data.content[:200]}",
            confidence=1.0,
            importance=1.2,
            source="auto",
            user_id=user.id
        )
    return note

@router.put("/{note_id}")
def update_note(note_id: int, data: KnowledgeNoteCreate, user: UserResponse = Depends(get_current_user)):
    success = NoteService.update_note(
        note_id=note_id,
        title=data.title,
        content=data.content,
        tags=data.tags or "",
        category=data.category or "general",
        user_id=user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "success", "id": note_id}

@router.delete("/{note_id}")
def delete_note(note_id: int, user: UserResponse = Depends(get_current_user)):
    success = NoteService.delete_note(note_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "success", "id": note_id}
