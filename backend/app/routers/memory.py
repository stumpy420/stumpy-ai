from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.models.memory import MemoryItem, TeachRequest, KnowledgeGraphResponse
from app.models.user import UserResponse
from app.services.memory_engine import MemoryEngine
from app.services.auth_service import get_current_user
from app.services.tier_service import TierService
from app.database import get_db_connection

router = APIRouter(prefix="/api/memory", tags=["Memory"])

@router.get("", response_model=List[MemoryItem])
def list_memories(category: Optional[str] = None, search: Optional[str] = None, user: UserResponse = Depends(get_current_user)):
    return MemoryEngine.get_all_memories(category=category, search=search, user_id=user.id)

@router.post("", response_model=MemoryItem)
def teach_memory(req: TeachRequest, user: UserResponse = Depends(get_current_user)):
    # Check Free tier memory limit
    TierService.check_memory_quota(user)

    return MemoryEngine.add_memory(
        category=req.category,
        topic=req.topic,
        content=req.content,
        confidence=1.0,
        importance=1.8,
        is_pinned=req.is_pinned,
        source="direct_teaching",
        user_id=user.id
    )

@router.put("/{mem_id}")
def update_memory(mem_id: int, req: TeachRequest, user: UserResponse = Depends(get_current_user)):
    success = MemoryEngine.update_memory(
        mem_id=mem_id,
        content=req.content,
        topic=req.topic,
        is_pinned=req.is_pinned,
        category=req.category,
        user_id=user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success", "id": mem_id}

@router.delete("/{mem_id}")
def delete_memory(mem_id: int, user: UserResponse = Depends(get_current_user)):
    success = MemoryEngine.delete_memory(mem_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success", "id": mem_id}

@router.post("/pin/{mem_id}")
def toggle_pin(mem_id: int, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_pinned FROM memories WHERE id = ? AND user_id = ?", (mem_id, user.id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Memory not found")

    new_pin = 0 if row["is_pinned"] else 1
    cursor.execute("UPDATE memories SET is_pinned = ? WHERE id = ? AND user_id = ?", (new_pin, mem_id, user.id))
    conn.commit()
    conn.close()
    return {"status": "success", "id": mem_id, "is_pinned": bool(new_pin)}

@router.get("/graph", response_model=KnowledgeGraphResponse)
def get_knowledge_graph(user: UserResponse = Depends(get_current_user)):
    return MemoryEngine.get_knowledge_graph(user_id=user.id)

@router.get("/profile")
def get_user_profile(user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY section, property_name", (user.id,))
    rows = cursor.fetchall()
    conn.close()

    profile = {}
    for r in rows:
        sec = r["section"]
        if sec not in profile:
            profile[sec] = {}
        profile[sec][r["property_name"]] = r["property_value"]

    return profile
