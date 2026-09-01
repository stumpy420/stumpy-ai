import re
import math
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database import get_db_connection
from app.models.memory import MemoryItem, KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphResponse

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", 
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", 
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", 
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", 
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", 
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", 
    "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

def tokenize(text: str) -> List[str]:
    text = text.lower()
    words = re.findall(r'\b[a-z0-9_\-\.]+\b', text)
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

class MemoryEngine:
    @staticmethod
    def add_memory(
        category: str,
        topic: str,
        content: str,
        confidence: float = 1.0,
        importance: float = 1.0,
        is_pinned: bool = False,
        source: str = "auto",
        user_id: int = 1
    ) -> MemoryItem:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            "SELECT id, content, importance, access_count FROM memories WHERE user_id = ? AND category = ? AND topic = ?",
            (user_id, category, topic)
        )
        existing = cursor.fetchone()

        if existing:
            mem_id = existing["id"]
            new_importance = max(existing["importance"], importance)
            cursor.execute("""
                UPDATE memories 
                SET content = ?, confidence = ?, importance = ?, is_pinned = ?, source = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (content, confidence, new_importance, 1 if is_pinned else 0, source, now, mem_id, user_id))
            conn.commit()
            conn.close()
            return MemoryItem(
                id=mem_id, category=category, topic=topic, content=content,
                confidence=confidence, importance=new_importance, access_count=existing["access_count"],
                is_pinned=is_pinned, source=source, created_at=now, updated_at=now
            )
        else:
            cursor.execute("""
                INSERT INTO memories (user_id, category, topic, content, confidence, importance, is_pinned, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, category, topic, content, confidence, importance, 1 if is_pinned else 0, source, now, now))
            mem_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return MemoryItem(
                id=mem_id, category=category, topic=topic, content=content,
                confidence=confidence, importance=importance, access_count=0,
                is_pinned=is_pinned, source=source, created_at=now, updated_at=now
            )

    @staticmethod
    def get_all_memories(category: Optional[str] = None, search: Optional[str] = None, user_id: int = 1) -> List[MemoryItem]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM memories WHERE user_id = ?"
        params = [user_id]

        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        
        if search:
            query += " AND (topic LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY is_pinned DESC, importance DESC, updated_at DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [
            MemoryItem(
                id=row["id"],
                category=row["category"],
                topic=row["topic"],
                content=row["content"],
                confidence=row["confidence"],
                importance=row["importance"],
                access_count=row["access_count"],
                is_pinned=bool(row["is_pinned"]),
                source=row["source"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    @staticmethod
    def recall_memories(query_text: str, limit: int = 6, user_id: int = 1) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE user_id = ?", (user_id,))
        all_memories = cursor.fetchall()

        if not all_memories:
            conn.close()
            return []

        query_tokens = set(tokenize(query_text))
        scored_memories = []
        now = datetime.utcnow()

        for mem in all_memories:
            doc_tokens = set(tokenize(mem["topic"] + " " + mem["content"]))
            if not doc_tokens:
                continue

            intersection = query_tokens.intersection(doc_tokens)
            score = len(intersection) / (math.sqrt(len(query_tokens) + 1) * math.sqrt(len(doc_tokens) + 1))

            lowered_query = query_text.lower()
            if mem["topic"].lower() in lowered_query:
                score += 0.4
            
            if mem["is_pinned"]:
                score += 0.25

            score *= (0.8 + 0.4 * mem["importance"])

            try:
                updated_at = datetime.fromisoformat(mem["updated_at"])
                days_old = (now - updated_at).total_seconds() / 86400.0
                recency_multiplier = math.exp(-days_old / 60.0)
                score *= (0.85 + 0.15 * recency_multiplier)
            except Exception:
                pass

            if mem["category"] == "identity" and len(query_tokens) > 0:
                score += 0.15

            if score > 0.05 or mem["is_pinned"] or mem["category"] == "preference":
                scored_memories.append((score, mem))

        scored_memories.sort(key=lambda x: x[0], reverse=True)
        top_memories = scored_memories[:limit]

        results = []
        for score, mem in top_memories:
            cursor.execute(
                "UPDATE memories SET access_count = access_count + 1 WHERE id = ? AND user_id = ?",
                (mem["id"], user_id)
            )
            results.append({
                "id": mem["id"],
                "category": mem["category"],
                "topic": mem["topic"],
                "content": mem["content"],
                "confidence": mem["confidence"],
                "importance": mem["importance"],
                "is_pinned": bool(mem["is_pinned"]),
                "source": mem["source"],
                "relevance_score": round(score, 3)
            })

        conn.commit()
        conn.close()
        return results

    @staticmethod
    def update_memory(mem_id: int, content: str, topic: Optional[str] = None, is_pinned: Optional[bool] = None, category: Optional[str] = None, user_id: int = 1) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        updates = ["content = ?", "updated_at = ?"]
        params = [content, now]

        if topic:
            updates.append("topic = ?")
            params.append(topic)
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            params.append(1 if is_pinned else 0)
        if category:
            updates.append("category = ?")
            params.append(category)

        params.extend([mem_id, user_id])
        cursor.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ? AND user_id = ?", tuple(params))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    @staticmethod
    def delete_memory(mem_id: int, user_id: int = 1) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (mem_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    @staticmethod
    def get_knowledge_graph(user_id: int = 1) -> KnowledgeGraphResponse:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM memories WHERE user_id = ? ORDER BY importance DESC", (user_id,))
        memories = cursor.fetchall()

        cursor.execute("SELECT * FROM skills WHERE user_id = ?", (user_id,))
        skills = cursor.fetchall()

        cursor.execute("SELECT * FROM knowledge_notes WHERE user_id = ?", (user_id,))
        notes = cursor.fetchall()

        conn.close()

        nodes: List[KnowledgeGraphNode] = []
        edges: List[KnowledgeGraphEdge] = []

        nodes.append(KnowledgeGraphNode(
            id="node_user",
            label="User Core Profile",
            category="user",
            importance=2.0,
            is_pinned=True,
            details="Central anchor representing your personalized preferences, goals, and learning journey."
        ))

        for mem in memories:
            node_id = f"mem_{mem['id']}"
            nodes.append(KnowledgeGraphNode(
                id=node_id,
                label=mem["topic"].replace("_", " ").title(),
                category=mem["category"],
                importance=mem["importance"],
                is_pinned=bool(mem["is_pinned"]),
                details=mem["content"]
            ))
            edges.append(KnowledgeGraphEdge(
                source="node_user",
                target=node_id,
                relationship=f"has_{mem['category']}",
                weight=mem["importance"]
            ))

        for sk in skills:
            sk_id = f"skill_{sk['id']}"
            nodes.append(KnowledgeGraphNode(
                id=sk_id,
                label=sk["name"],
                category="skill_tracker",
                importance=max(1.0, sk["mastery_level"] / 50.0),
                is_pinned=True,
                details=f"Mastery: {round(sk['mastery_level'], 1)}% | Quizzes: {sk['total_quizzes_taken']} ({sk['correct_answers']} correct)"
            ))
            edges.append(KnowledgeGraphEdge(
                source="node_user",
                target=sk_id,
                relationship="learning",
                weight=1.5
            ))

        for note in notes:
            node_id = f"note_{note['id']}"
            nodes.append(KnowledgeGraphNode(
                id=node_id,
                label=note["title"][:25],
                category="knowledge_note",
                importance=1.1,
                is_pinned=False,
                details=f"Tags: {note['tags']}\n{note['content'][:120]}..."
            ))
            edges.append(KnowledgeGraphEdge(
                source="node_user",
                target=node_id,
                relationship="stored_note",
                weight=1.0
            ))

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if nodes[i].id == "node_user" or nodes[j].id == "node_user":
                    continue
                tokens_i = set(tokenize(nodes[i].label + " " + nodes[i].details))
                tokens_j = set(tokenize(nodes[j].label + " " + nodes[j].details))
                overlap = tokens_i.intersection(tokens_j)
                if len(overlap) >= 2:
                    edges.append(KnowledgeGraphEdge(
                        source=nodes[i].id,
                        target=nodes[j].id,
                        relationship="relates_to",
                        weight=min(2.0, len(overlap) * 0.5)
                    ))

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "memories_count": len(memories),
            "skills_count": len(skills),
            "notes_count": len(notes)
        }

        return KnowledgeGraphResponse(nodes=nodes, edges=edges, stats=stats)
