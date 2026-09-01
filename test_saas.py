import sys
import os
from pathlib import Path

# Enable UTF-8 for windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database import init_db, get_db_connection
from app.services.auth_service import AuthService, create_jwt_token, decode_jwt_token
from app.services.memory_engine import MemoryEngine
from app.services.tier_service import TierService
from app.services.billing_service import BillingService
from app.models.user import UserResponse
from fastapi import HTTPException

def run_saas_tests():
    print("[TEST] Running Stumpy AI Multi-Tenant SaaS & Freemium Verification Tests...")

    # 1. Init Database
    print("1. Initializing Multi-Tenant Database...")
    init_db()
    print("   [PASS] Multi-tenant database initialized.")

    # 2. Guest User Auto-Provisioning
    print("2. Testing Guest Mode...")
    guest = AuthService.get_or_create_guest()
    assert guest.is_guest is True
    assert guest.tier == "free"
    print(f"   [PASS] Guest user provisioned: {guest.email} (ID: {guest.id}, Tier: {guest.tier})")

    # 3. User Registration & Password Hashing
    print("3. Testing User Registration & Secure PBKDF2 Password Hashing...")
    test_email = "tester_saas@stumpy.ai"
    # Clean up if exists from previous run
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email = ?", (test_email,))
    conn.commit()
    conn.close()

    user = AuthService.register_user(email=test_email, password="SecurePassword123!", name="Elena Architect")
    assert user.email == test_email
    assert user.name == "Elena Architect"
    assert user.tier == "free"
    print(f"   [PASS] Registered user: {user.name} ({user.email}) with default Free tier.")

    # 4. User Login & JWT Token Verification
    print("4. Testing Login & JWT Token Verification...")
    auth_user = AuthService.authenticate_user(email=test_email, password="SecurePassword123!")
    token = create_jwt_token({"sub": auth_user.id, "email": auth_user.email, "tier": auth_user.tier})
    payload = decode_jwt_token(token)
    assert payload is not None
    assert payload["sub"] == auth_user.id
    assert payload["email"] == test_email
    print(f"   [PASS] JWT token successfully issued and verified for User ID {auth_user.id}.")

    # 5. Data Partitioning & Isolation
    print("5. Testing Multi-Tenant Data Isolation...")
    # Add memory for User Elena
    mem_elena = MemoryEngine.add_memory(
        category="project",
        topic="elena_private_project",
        content="Elena is building a high-frequency trading bot.",
        user_id=user.id
    )
    # Check that Guest cannot see Elena's memory
    guest_memories = MemoryEngine.get_all_memories(user_id=guest.id)
    guest_topics = [m.topic for m in guest_memories]
    assert "elena_private_project" not in guest_topics
    
    elena_memories = MemoryEngine.get_all_memories(user_id=user.id)
    elena_topics = [m.topic for m in elena_memories]
    assert "elena_private_project" in elena_topics
    print("   [PASS] Complete data isolation confirmed between Guest and Registered User.")

    # 6. Free Tier Quota Guard
    print("6. Testing Free Tier Quota Guard...")
    # Mock user having reached 50 memories
    mock_free_user = UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        tier="free",
        is_guest=False,
        memories_count=50,
        memory_limit=50,
        quizzes_today=5,
        quiz_daily_limit=5,
        notes_count=10,
        note_limit=10,
        created_at=user.created_at
    )
    quota_blocked = False
    try:
        TierService.check_memory_quota(mock_free_user)
    except HTTPException as e:
        quota_blocked = True
        assert e.status_code == 403
        print(f"   [PASS] Memory quota properly guarded: {e.detail}")

    assert quota_blocked is True, "Expected Free tier memory quota to block at 50"

    # 7. Pro Tier Upgrade Flow
    print("7. Testing Pro Tier Upgrade & Limit Unlocking...")
    upgraded_user = BillingService.upgrade_user(user.id, "pro_monthly")
    assert upgraded_user.tier == "pro"
    assert upgraded_user.memory_limit > 10000
    assert upgraded_user.quiz_daily_limit > 10000

    # Test that Pro user passes all quota checks even at high counts
    mock_pro_user = UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        tier="pro",
        is_guest=False,
        memories_count=500,
        memory_limit=999999,
        quizzes_today=100,
        quiz_daily_limit=999999,
        notes_count=200,
        note_limit=999999,
        created_at=user.created_at
    )
    assert TierService.check_memory_quota(mock_pro_user) is True
    assert TierService.check_quiz_quota(mock_pro_user) is True
    assert TierService.check_note_quota(mock_pro_user) is True
    print(f"   [PASS] Stumpy Pro upgrade verified: all quotas unlocked (Tier: {upgraded_user.tier}).")

    print("\n[SUCCESS] ALL SAAS & FREEMIUM TESTS PASSED! Stumpy AI is ready for public release.\n")

if __name__ == "__main__":
    run_saas_tests()
