import re
from datetime import datetime
from typing import List, Dict, Any
from app.services.memory_engine import MemoryEngine
from app.database import get_db_connection

class ReflectionEngine:
    @staticmethod
    def extract_and_learn(user_message: str, assistant_response: str = "", user_id: int = 1) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        cleaned = user_message.strip()

        # 1. Identity Extraction
        name_match = re.search(r"\b(?:my name is|i am|i'm|call me)\s+([A-Z][a-zA-Z0-9_\-]+)", cleaned, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            if name.lower() not in {"learning", "trying", "building", "working", "a", "an", "the", "ready", "interested", "sure", "happy", "excited"}:
                MemoryEngine.add_memory(
                    category="identity",
                    topic="user_name",
                    content=f"User's name is {name}.",
                    confidence=0.95,
                    importance=1.8,
                    is_pinned=True,
                    source="auto",
                    user_id=user_id
                )
                insights.append({"category": "Identity", "topic": "User Name", "fact": f"Learned your name is {name}."})
                ReflectionEngine._update_profile("personal", "user_name", name, user_id)

        role_match = re.search(r"\bi am a\s+([a-zA-Z0-9\s\-]+?)(?:\.|,|\band\b|learning|building|working|who|$)", cleaned, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).strip()
            if len(role) > 2 and len(role.split()) <= 4 and role.lower() not in {"fan", "beginner", "student of"}:
                MemoryEngine.add_memory(
                    category="identity",
                    topic="user_role",
                    content=f"User is a {role}.",
                    confidence=0.9,
                    importance=1.4,
                    source="auto",
                    user_id=user_id
                )
                insights.append({"category": "Identity", "topic": "Role / Profession", "fact": f"Noted you are a {role}."})
                ReflectionEngine._update_profile("work", "user_role", role, user_id)

        # 2. Preference Extraction
        pref_matches = [
            (r"\bi prefer\s+([^\.]+?)(?:\.|$)", "preferred_approach"),
            (r"\bi always (?:use|prefer|write)\s+([^\.]+?)(?:\.|$)", "preferred_tool"),
            (r"\bmy favorite\s+([a-zA-Z0-9\s]+?)\s+is\s+([^\.]+?)(?:\.|$)", "favorite_item"),
            (r"\bi love\s+([^\.]+?)(?:\.|$)", "likes"),
            (r"\bi hate\s+([^\.]+?)(?:\.|$)", "dislikes"),
            (r"\bplease (?:keep|make) (?:answers|responses|it)\s+([^\.]+?)(?:\.|$)", "tone_preference")
        ]

        for pattern, topic in pref_matches:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    key = match.group(1).strip().replace(" ", "_")
                    val = match.group(2).strip()
                    content = f"User's favorite {key} is {val}."
                    topic_name = f"favorite_{key}"
                else:
                    val = match.group(1).strip()
                    content = f"User preference: {val}."
                    topic_name = topic

                if len(val) >= 3 and len(val) < 120:
                    MemoryEngine.add_memory(
                        category="preference",
                        topic=topic_name,
                        content=content,
                        confidence=0.9,
                        importance=1.3,
                        source="auto",
                        user_id=user_id
                    )
                    insights.append({"category": "Preference", "topic": topic_name.replace("_", " ").title(), "fact": content})

        # 3. Project Extraction
        proj_matches = [
            r"\bi'm building (?:a|an)\s+([^\.]+?)(?:\.|$|,|\busing\b|\bwith\b)",
            r"\bi am working on (?:a|an)?\s+([^\.]+?)(?:\.|$|,|\busing\b|\bwith\b)",
            r"\bmy project is (?:called\s+)?([^\.]+?)(?:\.|$|,)"
        ]
        for pattern in proj_matches:
            p_match = re.search(pattern, cleaned, re.IGNORECASE)
            if p_match:
                proj_desc = p_match.group(1).strip()
                if len(proj_desc) > 3 and len(proj_desc) < 140:
                    MemoryEngine.add_memory(
                        category="project",
                        topic="active_project",
                        content=f"User is building: {proj_desc}.",
                        confidence=0.92,
                        importance=1.5,
                        is_pinned=True,
                        source="auto",
                        user_id=user_id
                    )
                    insights.append({"category": "Project", "topic": "Active Project", "fact": f"Recorded active project: {proj_desc}."})
                    ReflectionEngine._update_profile("technical", "active_project", proj_desc, user_id)
                    break

        # 4. Learning & Skill Acquisition Extraction
        skill_matches = [
            r"\bi'm learning\s+([a-zA-Z0-9\+\#\s\.\-]+?)(?:\.|$|,|\band\b)",
            r"\bi am studying\s+([a-zA-Z0-9\+\#\s\.\-]+?)(?:\.|$|,|\band\b)",
            r"\bi want to master\s+([a-zA-Z0-9\+\#\s\.\-]+?)(?:\.|$|,|\band\b)",
            r"\bhelp me learn\s+([a-zA-Z0-9\+\#\s\.\-]+?)(?:\.|$|,|\band\b)"
        ]
        for pattern in skill_matches:
            s_match = re.search(pattern, cleaned, re.IGNORECASE)
            if s_match:
                skill_name = s_match.group(1).strip()
                skill_name = re.sub(r'^(about|how to|the|some)\s+', '', skill_name, flags=re.IGNORECASE).strip()
                if len(skill_name) >= 2 and len(skill_name) < 40:
                    MemoryEngine.add_memory(
                        category="skill",
                        topic=f"learning_{skill_name.lower().replace(' ', '_')}",
                        content=f"User is actively learning and practicing {skill_name}.",
                        confidence=0.95,
                        importance=1.4,
                        source="auto",
                        user_id=user_id
                    )
                    insights.append({"category": "Skill", "topic": "Learning Goal", "fact": f"Added '{skill_name}' to your learning targets."})
                    ReflectionEngine._ensure_skill_exists(skill_name, user_id)
                    break

        # 5. Direct Correction Detection
        correction_matches = [
            r"\b(?:actually|no|correction|wait),\s*(?:i switched|i changed|it's|it is|i meant|i use)\s+([^\.]+?)(?:\.|$)",
            r"\b(?:actually|correction),\s*([^\.]+?)(?:\.|$)"
        ]
        for pattern in correction_matches:
            c_match = re.search(pattern, cleaned, re.IGNORECASE)
            if c_match:
                corr = c_match.group(1).strip()
                if len(corr) > 3:
                    MemoryEngine.add_memory(
                        category="preference",
                        topic="user_correction",
                        content=f"User correction: {corr}.",
                        confidence=1.0,
                        importance=1.6,
                        is_pinned=True,
                        source="correction",
                        user_id=user_id
                    )
                    insights.append({"category": "Correction", "topic": "Updated Fact", "fact": f"Recorded correction: {corr}"})

        # 6. Direct "Remember..." instruction
        remember_match = re.search(r"\bremember (?:that\s+)?([^\.]+?)(?:\.|$)", cleaned, re.IGNORECASE)
        if remember_match:
            fact = remember_match.group(1).strip()
            if len(fact) > 3:
                MemoryEngine.add_memory(
                    category="preference",
                    topic="user_instructed_memory",
                    content=f"User instructed to remember: {fact}",
                    confidence=1.0,
                    importance=1.8,
                    is_pinned=True,
                    source="direct_teaching",
                    user_id=user_id
                )
                insights.append({"category": "Direct Memory", "topic": "Pinned Fact", "fact": f"Stored pinned memory: '{fact}'."})

        return insights

    @staticmethod
    def _update_profile(section: str, prop: str, value: str, user_id: int = 1):
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO user_profile (user_id, section, property_name, property_value, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, property_name) DO UPDATE SET property_value = excluded.property_value, updated_at = excluded.updated_at
        """, (user_id, section, prop, value, now))
        conn.commit()
        conn.close()

    @staticmethod
    def _ensure_skill_exists(skill_name: str, user_id: int = 1):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM skills WHERE user_id = ? AND LOWER(name) = ?", (user_id, skill_name.lower()))
        existing = cursor.fetchone()
        if not existing:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO skills (user_id, name, category, mastery_level, target_level, total_quizzes_taken, correct_answers, notes, created_at, updated_at)
                VALUES (?, ?, ?, 15.0, 100.0, 0, 0, ?, ?, ?)
            """, (user_id, skill_name.title(), 'General', f'Auto-tracked learning skill: {skill_name}', now, now))
            conn.commit()
        conn.close()
