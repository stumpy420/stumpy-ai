import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.models.chat import ChatRequest, ChatResponse, ChatMessage, FeedbackRequest, SessionItem
from app.models.user import UserResponse
from app.services.memory_engine import MemoryEngine
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.services.auth_service import get_current_user
from app.services.tier_service import TierService
from app.database import get_db_connection

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def send_chat_message(req: ChatRequest, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    # 1. Manage Session scoped by user_id
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        title = req.message.strip().split("\n")[0][:36]
        if len(title) > 30:
            title = title[:30] + "..."
        cursor.execute("""
            INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user.id, title or "New Conversation", now, now))
    else:
        cursor.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user.id))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user.id, "New Conversation", now, now))

    # 2. Extract facts & learn from message (Reflection Engine)
    learned_insights = []
    # Check if user has memory capacity before auto-extracting
    if user.tier == "pro" or user.memories_count < user.memory_limit:
        learned_insights = ReflectionEngine.extract_and_learn(req.message, user_id=user.id)

    # 3. Retrieve relevant memories (Hybrid Recall)
    recalled_memories = MemoryEngine.recall_memories(req.message, limit=6, user_id=user.id)

    # 4. Fetch recent chat history for context
    cursor.execute("""
        SELECT role, content FROM chat_messages
        WHERE session_id = ? AND user_id = ?
        ORDER BY id ASC LIMIT 10
    """, (session_id, user.id))
    history_rows = cursor.fetchall()
    history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

    # 5. Save user message to database
    cursor.execute("""
        INSERT INTO chat_messages (user_id, session_id, role, content, recalled_memories_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user.id, session_id, "user", req.message, json.dumps([]), now))
    conn.commit()

    # 6. Generate AI response via LLM service
    response_data = await LLMService.generate_response(
        user_message=req.message,
        chat_history=history,
        recalled_memories=recalled_memories,
        tone_override=req.tone_override,
        user_id=user.id
    )

    assistant_msg = response_data.get("message", "")
    followups = response_data.get("suggested_followups", [])

    # 7. Save assistant message with recalled memories
    cursor.execute("""
        INSERT INTO chat_messages (user_id, session_id, role, content, recalled_memories_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user.id, session_id, "assistant", assistant_msg, json.dumps(recalled_memories), datetime.utcnow().isoformat()))

    cursor.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ? AND user_id = ?", (datetime.utcnow().isoformat(), session_id, user.id))
    conn.commit()
    conn.close()

    return ChatResponse(
        session_id=session_id,
        message=assistant_msg,
        recalled_memories=recalled_memories,
        learned_insights=learned_insights,
        suggested_followups=followups
    )

@router.get("/sessions", response_model=List[SessionItem])
def get_sessions(user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.title, s.created_at, s.updated_at, COUNT(m.id) as message_count
        FROM chat_sessions s
        LEFT JOIN chat_messages m ON s.id = m.session_id
        WHERE s.user_id = ?
        GROUP BY s.id
        ORDER BY s.updated_at DESC
    """, (user.id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        SessionItem(
            id=r["id"],
            title=r["title"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            message_count=r["message_count"]
        )
        for r in rows
    ]

@router.post("/sessions", response_model=SessionItem)
def create_new_session(title: str = "New Conversation", user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, user.id, title, now, now))
    conn.commit()
    conn.close()

    return SessionItem(
        id=session_id,
        title=title,
        created_at=now,
        updated_at=now,
        message_count=0
    )

@router.get("/history/{session_id}")
def get_chat_history(session_id: str, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, session_id, role, content, recalled_memories_json, feedback_score, created_at
        FROM chat_messages
        WHERE session_id = ? AND user_id = ?
        ORDER BY id ASC
    """, (session_id, user.id))
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for r in rows:
        try:
            recalled = json.loads(r["recalled_memories_json"])
        except Exception:
            recalled = []
        messages.append({
            "id": r["id"],
            "session_id": r["session_id"],
            "role": r["role"],
            "content": r["content"],
            "recalled_memories": recalled,
            "feedback_score": r["feedback_score"],
            "created_at": r["created_at"]
        })
    return messages

@router.delete("/history/{session_id}")
def delete_session(session_id: str, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ? AND user_id = ?", (session_id, user.id))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user.id))
    conn.commit()
    conn.close()
    return {"status": "deleted", "session_id": session_id}

@router.post("/feedback")
def submit_feedback(fb: FeedbackRequest, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE chat_messages
        SET feedback_score = ?
        WHERE id = ? AND user_id = ?
    """, (fb.score, fb.message_id, user.id))

    if fb.correction_text and len(fb.correction_text.strip()) > 3:
        MemoryEngine.add_memory(
            category="preference",
            topic="user_feedback_correction",
            content=f"Feedback Correction: {fb.correction_text.strip()}",
            confidence=1.0,
            importance=1.7,
            is_pinned=True,
            source="correction",
            user_id=user.id
        )

    conn.commit()
    conn.close()
    return {"status": "success", "message_id": fb.message_id, "score": fb.score}
