import json
from fastapi import APIRouter, Depends
from app.models.settings import SettingsModel, SystemStats
from app.models.user import UserResponse
from app.config import DEFAULT_SETTINGS
from app.database import get_db_connection
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/settings", tags=["Settings & Stats"])

@router.get("", response_model=SettingsModel)
def get_settings(user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings WHERE user_id = ?", (user.id,))
    rows = cursor.fetchall()
    conn.close()

    res = dict(DEFAULT_SETTINGS)
    for r in rows:
        try:
            res[r["key"]] = json.loads(r["value"])
        except Exception:
            res[r["key"]] = r["value"]

    return SettingsModel(**res)

@router.post("")
def save_settings(settings: SettingsModel, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    settings_dict = settings.model_dump()

    for k, v in settings_dict.items():
        cursor.execute("""
            INSERT INTO settings (user_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value
        """, (user.id, k, json.dumps(v)))

    conn.commit()
    conn.close()
    return {"status": "success", "settings": settings_dict}

@router.get("/stats", response_model=SystemStats)
def get_system_stats(user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user.id,))
    total_memories = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ? AND is_pinned = 1", (user.id,))
    pinned_memories = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*), AVG(mastery_level) FROM skills WHERE user_id = ?", (user.id,))
    skill_row = cursor.fetchone()
    total_skills = skill_row[0] or 0
    avg_mastery = round(skill_row[1] or 0.0, 1)

    cursor.execute("SELECT COUNT(*) FROM knowledge_notes WHERE user_id = ?", (user.id,))
    total_notes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ? AND role = 'user'", (user.id,))
    total_chat_turns = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ? AND source IN ('auto', 'correction')", (user.id,))
    learned_insights_count = cursor.fetchone()[0]

    conn.close()

    return SystemStats(
        total_memories=total_memories,
        pinned_memories=pinned_memories,
        total_skills=total_skills,
        average_mastery=avg_mastery,
        total_notes=total_notes,
        total_chat_turns=total_chat_turns,
        learned_insights_count=learned_insights_count
    )
