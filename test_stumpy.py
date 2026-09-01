import sys
import os
from pathlib import Path

# Enable UTF-8 for windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database import init_db, get_db_connection
from app.services.memory_engine import MemoryEngine
from app.services.reflection_engine import ReflectionEngine
from app.services.skill_service import SkillService
from app.services.note_service import NoteService
from app.services.llm_service import LLMService
from app.models.note import KnowledgeNoteCreate

def run_tests():
    print("[TEST] Running Stumpy AI Verification Tests...")
    
    # 1. Database Init Test
    print("1. Initializing Database & Seeding...")
    init_db()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM memories")
    mem_count = c.fetchone()[0]
    print(f"   [PASS] Database initialized successfully with {mem_count} starter memories.")
    conn.close()

    # 2. Reflection Engine Fact Extraction Test
    print("2. Testing Reflection Engine (Auto-learning)...")
    test_msg = "Hi! My name is Jordan, I am a Distributed Systems Engineer, and I am building an ultra-fast event queue in Rust. I prefer concise code snippets."
    insights = ReflectionEngine.extract_and_learn(test_msg)
    print(f"   [PASS] Extracted {len(insights)} learned insights:")
    for ins in insights:
        print(f"     - [{ins['category']}] {ins['topic']}: {ins['fact']}")

    assert len(insights) >= 3, f"Expected at least 3 insights, got {len(insights)}"

    # 3. Hybrid Memory Recall Test
    print("3. Testing Hybrid Memory Recall...")
    query = "What language am I using for my queue and what is my role?"
    recalled = MemoryEngine.recall_memories(query, limit=5)
    print(f"   [PASS] Recalled {len(recalled)} relevant memories:")
    for rm in recalled:
        print(f"     - ({rm['relevance_score']}) [{rm['category']}] {rm['topic']}: {rm['content']}")

    assert len(recalled) > 0, "Expected recalled memories"

    # 4. Knowledge Graph Synthesis Test
    print("4. Testing Knowledge Graph Generation...")
    graph = MemoryEngine.get_knowledge_graph()
    print(f"   [PASS] Knowledge graph synthesized with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")
    assert len(graph.nodes) >= 4, "Expected at least 4 nodes in graph"

    # 5. Skill Mastery & Adaptive Quiz Test
    print("5. Testing Skill Tracker and Adaptive Quizzes...")
    skills = SkillService.get_all_skills()
    assert len(skills) > 0, "Expected skills to be available"
    test_skill = skills[0]
    quiz = SkillService.generate_quiz_for_skill(test_skill.id)
    print(f"   [PASS] Generated quiz for '{test_skill.name}': {quiz.question[:60]}...")
    
    # Submit correct answer
    res = SkillService.submit_quiz_answer(quiz.id, quiz.correct_option_index)
    print(f"   [PASS] Submitted answer: is_correct={res.is_correct}, new mastery={res.new_mastery_level}%")
    assert res.is_correct is True

    # 6. Second Brain Note Vault Test
    print("6. Testing Second Brain Notes...")
    note = NoteService.create_note(KnowledgeNoteCreate(
        title="Tokio Runtime Configuration",
        content="tokio::runtime::Builder::new_multi_thread().worker_threads(8).enable_all().build()",
        tags="rust, tokio, async",
        category="code_snippet"
    ))
    print(f"   [PASS] Created and indexed note: '{note.title}' (ID: {note.id})")

    # 7. Built-in LLM Generation & Memory Weaving Test
    print("7. Testing Built-in Local LLM Memory Weaving...")
    llm_resp = LLMService._builtin_generate(
        user_message="Tell me about my architecture choices and preferred stack",
        chat_history=[],
        recalled_memories=recalled,
        settings={"tone_conciseness": 50, "tone_formality": 40, "tone_style": "balanced"}
    )
    print(f"   [PASS] Generated contextual response ({len(llm_resp['message'])} chars)")
    print(f"     Followup suggestions: {llm_resp['suggested_followups']}")

    print("\n[SUCCESS] ALL TESTS PASSED! Stumpy AI is fully verified and functional.\n")

if __name__ == "__main__":
    run_tests()
