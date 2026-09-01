from datetime import datetime
from typing import List
from app.database import get_db_connection
from app.models.user import TierPlan, UserResponse
from app.services.auth_service import AuthService

TIER_PLANS = [
    TierPlan(
        id="free",
        name="Free Starter",
        price="$0",
        billing_period="forever",
        badge="🆓 Free",
        description="Perfect for exploring adaptive learning and lightweight daily assistance.",
        features=[
            "Up to 50 active memories in Brain",
            "5 Adaptive Skill Quizzes per day",
            "10 Second Brain notes",
            "Built-in Smart Adaptive AI Engine",
            "Interactive 2D Knowledge Graph",
            "Local SQLite data persistence"
        ],
        is_popular=False,
        limits={"memories": 50, "quizzes_daily": 5, "notes": 10, "models": ["builtin"]}
    ),
    TierPlan(
        id="pro_monthly",
        name="Stumpy Pro",
        price="$12",
        billing_period="per month",
        badge="🌟 PRO",
        description="Unlimited memory, deep reflection, premium cloud LLMs, and infinite skill mastery.",
        features=[
            "✨ Unlimited persistent memories & facts",
            "✨ Unlimited daily adaptive quizzes",
            "✨ Unlimited Second Brain knowledge vault",
            "✨ Google Gemini 2.0 & GPT-4o integration",
            "✨ High-priority response generation",
            "✨ Full custom persona & tone synthesis",
            "✨ Exportable HD Knowledge Graph data",
            "✨ Early access to upcoming voice & vision skills"
        ],
        is_popular=True,
        limits={"memories": "Unlimited", "quizzes_daily": "Unlimited", "notes": "Unlimited", "models": ["builtin", "gemini", "openai"]}
    )
]

class BillingService:
    @staticmethod
    def get_plans() -> List[TierPlan]:
        return TIER_PLANS

    @staticmethod
    def upgrade_user(user_id: int, plan_id: str = "pro_monthly") -> UserResponse:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE users
            SET tier = 'pro', updated_at = ?
            WHERE id = ?
        """, (now, user_id))

        conn.commit()
        conn.close()

        return AuthService.get_user_by_id(user_id)

    @staticmethod
    def cancel_subscription(user_id: int) -> UserResponse:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE users
            SET tier = 'free', updated_at = ?
            WHERE id = ?
        """, (now, user_id))

        conn.commit()
        conn.close()

        return AuthService.get_user_by_id(user_id)
