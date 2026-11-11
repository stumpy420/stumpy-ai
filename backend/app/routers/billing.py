from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
import stripe

from app.models.user import TierPlan, UpgradeRequest, UserResponse
from app.services.billing_service import BillingService, STRIPE_WEBHOOK_SECRET
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])


@router.get("/tiers", response_model=List[TierPlan])
def get_tiers():
    return BillingService.get_plans()


@router.post("/upgrade")
def upgrade_subscription(req: UpgradeRequest, user: UserResponse = Depends(get_current_user)):
    """
    If Stripe is configured: creates a Stripe Checkout session and returns { checkout_url }.
    If Stripe is NOT configured: instantly upgrades the user (demo mode).
    """
    if stripe.api_key and req.payment_method != "mock_instant":
        try:
            checkout_url = BillingService.create_checkout_session(user.id, user.email)
            return {"checkout_url": checkout_url}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Demo / test mode — instant upgrade
        updated_user = BillingService.upgrade_user(user.id, req.plan_id)
        return updated_user


@router.post("/cancel")
def cancel_subscription(user: UserResponse = Depends(get_current_user)):
    """
    If user has a Stripe subscription: redirects to Stripe Customer Portal.
    Otherwise: instantly cancels (demo mode).
    """
    if stripe.api_key:
        try:
            portal_url = BillingService.create_customer_portal_session(user.id)
            return {"portal_url": portal_url}
        except ValueError:
            # No Stripe customer — use legacy cancel
            updated_user = BillingService.cancel_subscription(user.id)
            return updated_user
    else:
        updated_user = BillingService.cancel_subscription(user.id)
        return updated_user


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe sends payment events here. This endpoint:
    - Verifies the webhook signature
    - Upgrades user on successful payment
    - Downgrades user if subscription is cancelled
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        return JSONResponse({"error": "Webhook secret not configured"}, status_code=500)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        BillingService.handle_checkout_completed(session)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        BillingService.handle_subscription_deleted(subscription)

    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        # If subscription status changed to cancelled/unpaid
        if subscription.get("status") in ("canceled", "unpaid"):
            BillingService.handle_subscription_deleted(subscription)

    return {"status": "ok"}
