from fastapi import APIRouter, Depends, HTTPException
from app.models.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService, create_jwt_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication & User"])

@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister):
    user = AuthService.register_user(email=data.email, password=data.password, name=data.name)
    token = create_jwt_token({"sub": user.id, "email": user.email, "tier": user.tier})
    return TokenResponse(access_token=token, user=user)

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    user = AuthService.authenticate_user(email=data.email, password=data.password)
    token = create_jwt_token({"sub": user.id, "email": user.email, "tier": user.tier})
    return TokenResponse(access_token=token, user=user)

@router.get("/guest", response_model=TokenResponse)
def get_guest_session():
    user = AuthService.get_or_create_guest()
    token = create_jwt_token({"sub": user.id, "email": user.email, "tier": user.tier})
    return TokenResponse(access_token=token, user=user)

@router.get("/me", response_model=UserResponse)
def get_me(user: UserResponse = Depends(get_current_user)):
    return user
