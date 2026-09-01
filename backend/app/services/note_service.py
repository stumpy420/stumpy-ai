from datetime import datetime
from typing import List, Optional
from app.database import get_db_connection
from app.models.note import KnowledgeNoteItem, KnowledgeNoteCreate

class NoteService:
    @staticmethod
    def get_all_notes(search: Optional[str] = None, tag: Optional[str] = None, user_id: int = 1) -> List[KnowledgeNoteItem]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM knowledge_notes WHERE user_id = ?"
        params = [user_id]

        if search:
            query += " AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")

        query += " ORDER BY updated_at DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [
            KnowledgeNoteItem(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                tags=row["tags"] or "",
                category=row["category"] or "general",
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    @staticmethod
    def create_note(data: KnowledgeNoteCreate, user_id: int = 1) -> KnowledgeNoteItem:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO knowledge_notes (user_id, title, content, tags, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, data.title, data.content, data.tags or "", data.category or "general", now, now))
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return KnowledgeNoteItem(
            id=note_id,
            title=data.title,
            content=data.content,
            tags=data.tags or "",
            category=data.category or "general",
            created_at=now,
            updated_at=now
        )

    @staticmethod
    def update_note(note_id: int, title: str, content: str, tags: str, category: str, user_id: int = 1) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE knowledge_notes
            SET title = ?, content = ?, tags = ?, category = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (title, content, tags, category, now, note_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    @staticmethod
    def delete_note(note_id: int, user_id: int = 1) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
