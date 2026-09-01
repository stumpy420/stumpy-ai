import sqlite3
import json
from datetime import datetime
from app.config import DB_PATH, DEFAULT_SETTINGS

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        tier TEXT DEFAULT 'free',
        is_guest INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 2. Memories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        category TEXT NOT NULL,
        topic TEXT NOT NULL,
        content TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        importance REAL DEFAULT 1.0,
        access_count INTEGER DEFAULT 0,
        is_pinned INTEGER DEFAULT 0,
        source TEXT DEFAULT 'auto',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 3. User Profile
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        section TEXT NOT NULL,
        property_name TEXT NOT NULL,
        property_value TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, property_name)
    );
    """)

    # 4. Skills
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        mastery_level REAL DEFAULT 10.0,
        target_level REAL DEFAULT 100.0,
        total_quizzes_taken INTEGER DEFAULT 0,
        correct_answers INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, name)
    );
    """)

    # 5. Quizzes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        skill_id INTEGER,
        question TEXT NOT NULL,
        options_json TEXT NOT NULL,
        correct_option_index INTEGER NOT NULL,
        explanation TEXT NOT NULL,
        difficulty TEXT DEFAULT 'intermediate',
        user_answered_index INTEGER,
        is_correct INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE
    );
    """)

    # 6. Knowledge Notes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT DEFAULT '',
        category TEXT DEFAULT 'general',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 7. Chat Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER DEFAULT 1,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 8. Chat Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        recalled_memories_json TEXT DEFAULT '[]',
        feedback_score INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
    );
    """)

    # 9. Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        UNIQUE(user_id, key)
    );
    """)

    # Migration: Check if skills table has single-column unique constraint on name
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='skills'")
        skill_schema = cursor.fetchone()
        if skill_schema and "name TEXT UNIQUE" in skill_schema[0]:
            cursor.execute("CREATE TABLE IF NOT EXISTS skills_temp AS SELECT * FROM skills;")
            cursor.execute("DROP TABLE skills;")
            cursor.execute("""
                CREATE TABLE skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    mastery_level REAL DEFAULT 10.0,
                    target_level REAL DEFAULT 100.0,
                    total_quizzes_taken INTEGER DEFAULT 0,
                    correct_answers INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, name)
                );
            """)
            cursor.execute("INSERT OR IGNORE INTO skills SELECT * FROM skills_temp;")
            cursor.execute("DROP TABLE skills_temp;")
    except Exception:
        pass

    # Migration: Check if user_profile table has composite unique on (user_id, property_name)
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_profile'")
        prof_schema = cursor.fetchone()
        if prof_schema and "property_name TEXT UNIQUE" in prof_schema[0]:
            cursor.execute("CREATE TABLE IF NOT EXISTS user_profile_temp AS SELECT * FROM user_profile;")
            cursor.execute("DROP TABLE user_profile;")
            cursor.execute("""
                CREATE TABLE user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    section TEXT NOT NULL,
                    property_name TEXT NOT NULL,
                    property_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, property_name)
                );
            """)
            cursor.execute("INSERT OR IGNORE INTO user_profile SELECT * FROM user_profile_temp;")
            cursor.execute("DROP TABLE user_profile_temp;")
    except Exception:
        pass

    # Ensure default guest exists
    cursor.execute("SELECT id FROM users WHERE id = 1")
    if not cursor.fetchone():
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, name, tier, is_guest, created_at, updated_at)
            VALUES (1, 'guest@stumpy.ai', 'guest_mode_unhashed', 'Guest Explorer', 'free', 1, ?, ?)
        """, (now, now))

    conn.commit()
    conn.close()

    # Ensure starter data for user 1 is populated
    seed_starter_data_for_user(1)

def seed_starter_data_for_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Starter memories
    cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] == 0:
        starter_memories = [
            (user_id, 'identity', 'ai_name', 'My name is Stumpy AI, your personal adaptive AI companion.', 1.0, 2.0, 1, 'system', now, now),
            (user_id, 'identity', 'core_mission', 'I continuously adapt to your tone, remember your projects, and help you master new skills.', 1.0, 2.0, 1, 'system', now, now),
            (user_id, 'preference', 'learning_style', 'User loves clear, intuitive explanations with practical examples.', 0.9, 1.2, 1, 'auto', now, now),
            (user_id, 'skill', 'starter_track', 'User is exploring adaptive AI, coding, and continuous learning systems.', 0.85, 1.0, 0, 'auto', now, now),
        ]
        cursor.executemany("""
            INSERT INTO memories (user_id, category, topic, content, confidence, importance, is_pinned, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, starter_memories)

    # Starter skills
    cursor.execute("SELECT COUNT(*) FROM skills WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT OR IGNORE INTO skills (user_id, name, category, mastery_level, target_level, total_quizzes_taken, correct_answers, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, 'Modern Python & AI Systems', 'Programming', 45.0, 100.0, 2, 1, 'Async Python, FastAPI, and memory embeddings', now, now))
        
        cursor.execute("""
            INSERT OR IGNORE INTO skills (user_id, name, category, mastery_level, target_level, total_quizzes_taken, correct_answers, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, 'System Design & Scalability', 'DevOps', 30.0, 100.0, 1, 0, 'Microservices, caching strategies, and vector indices', now, now))

    # Starter settings
    for k, v in DEFAULT_SETTINGS.items():
        cursor.execute("SELECT 1 FROM settings WHERE user_id = ? AND key = ?", (user_id, k))
        if not cursor.fetchone():
            cursor.execute("INSERT OR IGNORE INTO settings (user_id, key, value) VALUES (?, ?, ?)", (user_id, k, json.dumps(v)))

    conn.commit()
    conn.close()
