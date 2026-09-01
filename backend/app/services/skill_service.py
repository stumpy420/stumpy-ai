import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database import get_db_connection
from app.models.skill import SkillItem, QuizQuestion, QuizResult

QUESTION_BANK = {
    "python": [
        {
            "question": "What is the primary difference between `asyncio.gather()` and `asyncio.wait()` in Python?",
            "options": [
                "`gather()` returns results in submission order and aggregates exceptions, while `wait()` returns sets of done/pending tasks with configurable return conditions.",
                "`gather()` creates OS threads while `wait()` uses green threads.",
                "`gather()` is only for synchronous functions, while `wait()` is for async coroutines.",
                "`wait()` is deprecated in modern Python 3.11+."
            ],
            "correct_index": 0,
            "explanation": "`asyncio.gather()` returns futures in order, whereas `asyncio.wait()` returns (done, pending) sets and allows `FIRST_COMPLETED` or `ALL_COMPLETED` conditions.",
            "difficulty": "intermediate"
        },
        {
            "question": "In Pydantic v2, which method is used to parse and validate a raw JSON string into a model instance?",
            "options": [
                "`Model.model_validate_json(raw_str)`",
                "`Model.parse_raw_json(raw_str)`",
                "`Model.from_json(raw_str)`",
                "`Model.validate_json(raw_str)`"
            ],
            "correct_index": 0,
            "explanation": "Pydantic v2 replaced `parse_raw` with `model_validate_json` for high-performance Rust-core validation.",
            "difficulty": "intermediate"
        },
        {
            "question": "What is the time complexity of looking up a key in a standard Python dictionary in the average case?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            "correct_index": 0,
            "explanation": "Python dictionaries use a hash table implementation that provides O(1) average time complexity for lookups.",
            "difficulty": "beginner"
        }
    ],
    "rust": [
        {
            "question": "In Rust, what is the main purpose of the `Arc<T>` type compared to `Rc<T>`?",
            "options": [
                "`Arc<T>` provides thread-safe atomic reference counting, whereas `Rc<T>` is not thread-safe (does not implement Send/Sync).",
                "`Arc<T>` allows mutable borrowing across threads without a Mutex.",
                "`Arc<T>` operates on stack memory, while `Rc<T>` operates on heap.",
                "`Arc<T>` is only available in `no_std` environments."
            ],
            "correct_index": 0,
            "explanation": "`Arc` stands for Atomically Reference Counted and uses atomic primitives to allow safe sharing across multiple threads.",
            "difficulty": "intermediate"
        },
        {
            "question": "Which trait in Rust must a type implement to allow deep duplication of its data via `.clone()`?",
            "options": ["`Clone`", "`Copy`", "`Duplicate`", "`Send`"],
            "correct_index": 0,
            "explanation": "The `Clone` trait defines explicit duplication via `.clone()`. `Copy` is for implicit bitwise copies.",
            "difficulty": "beginner"
        }
    ],
    "system design": [
        {
            "question": "Which caching eviction policy removes the items that haven't been requested for the longest period of time?",
            "options": [
                "Least Recently Used (LRU)",
                "First In First Out (FIFO)",
                "Least Frequently Used (LFU)",
                "Random Replacement (RR)"
            ],
            "correct_index": 0,
            "explanation": "LRU discards the least recently accessed items first, commonly implemented using a Doubly Linked List + Hash Map.",
            "difficulty": "beginner"
        },
        {
            "question": "According to the CAP Theorem, what three guarantees are distributed systems forced to balance, being able to achieve at most two simultaneously?",
            "options": [
                "Consistency, Availability, Partition Tolerance",
                "Concurrency, Atomicity, Performance",
                "Caching, Availability, Persistence",
                "Capacity, Accuracy, Parallelism"
            ],
            "correct_index": 0,
            "explanation": "CAP stands for Consistency, Availability, and Partition Tolerance in distributed data stores.",
            "difficulty": "beginner"
        }
    ]
}

class SkillService:
    @staticmethod
    def get_all_skills(user_id: int = 1) -> List[SkillItem]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE user_id = ? ORDER BY mastery_level DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            SkillItem(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                mastery_level=row["mastery_level"],
                target_level=row["target_level"],
                total_quizzes_taken=row["total_quizzes_taken"],
                correct_answers=row["correct_answers"],
                notes=row["notes"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    @staticmethod
    def create_skill(name: str, category: str = "Programming", notes: str = "", user_id: int = 1) -> SkillItem:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO skills (user_id, name, category, mastery_level, target_level, total_quizzes_taken, correct_answers, notes, created_at, updated_at)
            VALUES (?, ?, ?, 10.0, 100.0, 0, 0, ?, ?, ?)
        """, (user_id, name, category, notes, now, now))
        skill_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return SkillItem(
            id=skill_id, name=name, category=category, mastery_level=10.0,
            target_level=100.0, total_quizzes_taken=0, correct_answers=0,
            notes=notes, created_at=now, updated_at=now
        )

    @staticmethod
    def generate_quiz_for_skill(skill_id: int, user_id: int = 1) -> QuizQuestion:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE id = ? AND user_id = ?", (skill_id, user_id))
        skill = cursor.fetchone()
        if not skill:
            conn.close()
            raise ValueError(f"Skill with ID {skill_id} not found.")

        skill_name = skill["name"]
        skill_key = skill_name.lower()
        
        matched_pool = []
        for key, questions in QUESTION_BANK.items():
            if key in skill_key or any(w in skill_key for w in key.split()):
                matched_pool.extend(questions)

        if not matched_pool:
            matched_pool = [
                {
                    "question": f"When architecting scalable applications in {skill_name}, which practice best ensures reliability and maintainability?",
                    "options": [
                        "Enforcing clear boundary abstractions, unit/integration testing, and decoupled state management.",
                        "Writing all logic into a single monolithic script to eliminate network overhead.",
                        "Disabling error checking in production environments for throughput.",
                        "Relying solely on in-memory storage without persistent logging."
                    ],
                    "correct_index": 0,
                    "explanation": f"In {skill_name}, proper modularity, state isolation, and comprehensive test coverage prevent cascading failures and facilitate long-term maintenance.",
                    "difficulty": "intermediate"
                },
                {
                    "question": f"What is a core benefit of adopting automated telemetry and structured logging in a {skill_name} workflow?",
                    "options": [
                        "Enables real-time observability, rapid root-cause diagnosis, and performance bottleneck tracking.",
                        "Guarantees 100% bug-free deployment automatically.",
                        "Replaces the need for code reviews and type checkers.",
                        "Reduces compiled binary size."
                    ],
                    "correct_index": 0,
                    "explanation": "Observability and structured logging provide crucial insights into runtime execution health, error rates, and latency profiles.",
                    "difficulty": "beginner"
                }
            ]

        selected = random.choice(matched_pool)
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO quizzes (user_id, skill_id, question, options_json, correct_option_index, explanation, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            skill_id,
            selected["question"],
            json.dumps(selected["options"]),
            selected["correct_index"],
            selected["explanation"],
            selected.get("difficulty", "intermediate"),
            now
        ))
        quiz_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return QuizQuestion(
            id=quiz_id,
            skill_id=skill_id,
            skill_name=skill_name,
            question=selected["question"],
            options=selected["options"],
            correct_option_index=selected["correct_index"],
            explanation=selected["explanation"],
            difficulty=selected.get("difficulty", "intermediate")
        )

    @staticmethod
    def submit_quiz_answer(quiz_id: int, user_option_index: int, user_id: int = 1) -> QuizResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quizzes WHERE id = ? AND user_id = ?", (quiz_id, user_id))
        quiz = cursor.fetchone()
        if not quiz:
            conn.close()
            raise ValueError(f"Quiz with ID {quiz_id} not found.")

        is_correct = (user_option_index == quiz["correct_option_index"])
        cursor.execute("""
            UPDATE quizzes
            SET user_answered_index = ?, is_correct = ?
            WHERE id = ? AND user_id = ?
        """, (user_option_index, 1 if is_correct else 0, quiz_id, user_id))

        skill_id = quiz["skill_id"]
        cursor.execute("SELECT * FROM skills WHERE id = ? AND user_id = ?", (skill_id, user_id))
        skill = cursor.fetchone()

        new_mastery = skill["mastery_level"]
        total_quizzes = skill["total_quizzes_taken"] + 1
        correct_count = skill["correct_answers"] + (1 if is_correct else 0)

        if is_correct:
            boost = max(4.0, (100.0 - new_mastery) * 0.15)
            new_mastery = min(100.0, new_mastery + boost)
        else:
            new_mastery = max(5.0, new_mastery - 2.0)

        now = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE skills
            SET mastery_level = ?, total_quizzes_taken = ?, correct_answers = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (round(new_mastery, 1), total_quizzes, correct_count, now, skill_id, user_id))

        conn.commit()
        conn.close()

        streak_bonus = "🔥 Great job! Mastery increased!" if is_correct else "💡 Good try! Review the explanation to master this concept."

        return QuizResult(
            quiz_id=quiz_id,
            is_correct=is_correct,
            correct_option_index=quiz["correct_option_index"],
            explanation=quiz["explanation"],
            new_mastery_level=round(new_mastery, 1),
            streak_bonus=streak_bonus
        )
