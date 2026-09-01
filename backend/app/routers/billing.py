from typing import List
from fastapi import APIRouter, Depends
from app.models.user import TierPlan, UpgradeRequest, UserResponse
from app.services.billing_service import BillingService
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])

@router.get("/tiers", response_model=List[TierPlan])
def get_tiers():
    return BillingService.get_plans()

@router.post("/upgrade", response_model=UserResponse)
def upgrade_subscription(req: UpgradeRequest, user: UserResponse = Depends(get_current_user)):
    # Handle instant upgrade or Stripe checkout session creation
    updated_user = BillingService.upgrade_user(user.id, req.plan_id)
    return updated_user

@router.post("/cancel", response_model=UserResponse)
def cancel_subscription(user: UserResponse = Depends(get_current_user)):
    updated_user = BillingService.cancel_subscription(user.id)
    return updated_user
