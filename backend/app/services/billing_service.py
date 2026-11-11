import os
import stripe
from datetime import datetime
from typing import List, Optional
from app.database import get_db_connection
from app.models.user import TierPlan, UserResponse
from app.services.auth_service import AuthService

# -------------------------------------------------------------------
# Stripe Configuration
# Set these as environment variables in Railway:
#   STRIPE_SECRET_KEY      = sk_live_...  (or sk_test_... for testing)
#   STRIPE_WEBHOOK_SECRET  = whsec_...
#   STRIPE_PRICE_ID        = price_...    (your $12/mo Pro price ID)
#   APP_URL                = https://web-production-66a7b.up.railway.app
# -------------------------------------------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
APP_URL = os.getenv("APP_URL", "https://web-production-66a7b.up.railway.app")

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
    def create_checkout_session(user_id: int, user_email: str) -> str:
        """
        Creates a Stripe Checkout Session and returns the URL.
        The user gets redirected to Stripe's hosted payment page.
        """
        if not stripe.api_key or not STRIPE_PRICE_ID:
            raise ValueError(
                "Stripe is not configured. Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID in Railway environment variables."
            )

        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=user_email,
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1
            }],
            success_url=f"{APP_URL}/?upgrade=success",
            cancel_url=f"{APP_URL}/?upgrade=cancelled",
            metadata={
                "stumpy_user_id": str(user_id)
            },
            subscription_data={
                "metadata": {
                    "stumpy_user_id": str(user_id)
                }
            }
        )

        # Store the Stripe customer info for later reference
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET stripe_checkout_session_id = ?, updated_at = ?
            WHERE id = ?
        """, (session.id, datetime.utcnow().isoformat(), user_id))
        conn.commit()
        conn.close()

        return session.url

    @staticmethod
    def create_customer_portal_session(user_id: int) -> str:
        """
        Creates a Stripe Customer Portal session so users can manage
        their subscription, update payment method, or cancel.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT stripe_customer_id FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row["stripe_customer_id"]:
            raise ValueError("No Stripe customer found. User has not subscribed yet.")

        session = stripe.billing_portal.Session.create(
            customer=row["stripe_customer_id"],
            return_url=f"{APP_URL}/"
        )
        return session.url

    @staticmethod
    def handle_checkout_completed(session: dict):
        """
        Called by the webhook when a checkout.session.completed event fires.
        Upgrades the user to Pro and stores their Stripe customer/subscription IDs.
        """
        user_id = session.get("metadata", {}).get("stumpy_user_id")
        if not user_id:
            print("[Stripe Webhook] No stumpy_user_id in session metadata, skipping.")
            return

        user_id = int(user_id)
        customer_id = session.get("customer", "")
        subscription_id = session.get("subscription", "")
        now = datetime.utcnow().isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET tier = 'pro',
                stripe_customer_id = ?,
                stripe_subscription_id = ?,
                updated_at = ?
            WHERE id = ?
        """, (customer_id, subscription_id, now, user_id))
        conn.commit()
        conn.close()

        print(f"[Stripe] ✅ User {user_id} upgraded to Pro (sub: {subscription_id})")

    @staticmethod
    def handle_subscription_deleted(subscription: dict):
        """
        Called by the webhook when a customer.subscription.deleted event fires.
        Downgrades the user back to Free.
        """
        user_id = subscription.get("metadata", {}).get("stumpy_user_id")
        if not user_id:
            # Fallback: find user by stripe subscription ID
            sub_id = subscription.get("id", "")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE stripe_subscription_id = ?", (sub_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                user_id = row["id"]
            else:
                print(f"[Stripe Webhook] Cannot find user for subscription {sub_id}, skipping.")
                return

        user_id = int(user_id)
        now = datetime.utcnow().isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET tier = 'free',
                stripe_subscription_id = NULL,
                updated_at = ?
            WHERE id = ?
        """, (now, user_id))
        conn.commit()
        conn.close()

        print(f"[Stripe] ⬇️ User {user_id} downgraded to Free (subscription cancelled)")

    # --- Legacy fallback methods (used if Stripe is not configured) ---

    @staticmethod
    def upgrade_user(user_id: int, plan_id: str = "pro_monthly") -> UserResponse:
        """Instant upgrade without Stripe (for testing or if Stripe is not set up)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("UPDATE users SET tier = 'pro', updated_at = ? WHERE id = ?", (now, user_id))
        conn.commit()
        conn.close()
        return AuthService.get_user_by_id(user_id)

    @staticmethod
    def cancel_subscription(user_id: int) -> UserResponse:
        """Instant cancel without Stripe (for testing or if Stripe is not set up)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("UPDATE users SET tier = 'free', updated_at = ? WHERE id = ?", (now, user_id))
        conn.commit()
        conn.close()
        return AuthService.get_user_by_id(user_id)
