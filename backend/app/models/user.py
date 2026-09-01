from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = "Adventurer"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    tier: str  # 'free' or 'pro'
    is_guest: bool = False
    memories_count: int = 0
    memory_limit: int = 50
    quizzes_today: int = 0
    quiz_daily_limit: int = 5
    notes_count: int = 0
    note_limit: int = 10
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TierPlan(BaseModel):
    id: str
    name: str
    price: str
    billing_period: str
    badge: str
    description: str
    features: List[str]
    is_popular: bool = False
    limits: Dict[str, Any]

class UpgradeRequest(BaseModel):
    plan_id: str = "pro_monthly"
    payment_method: Optional[str] = "mock_instant"  # 'mock_instant' or 'stripe'
