import hashlib
import hmac
import os
import json
import base64
import time
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db_connection, seed_starter_data_for_user
from app.models.user import UserResponse

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "stumpy-super-secret-production-key-2026")
security = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${base64.b64encode(key).decode('utf-8')}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, stored_hash = hashed.split('$')
        computed = hash_password(password, salt)
        return hmac.compare_digest(computed, hashed)
    except Exception:
        return False

def create_jwt_token(payload: dict, expires_in_seconds: int = 86400 * 30) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = dict(payload)
    payload_copy["exp"] = int(time.time()) + expires_in_seconds

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode('utf-8')).decode('utf-8').rstrip('=')

    signature_raw = hmac.new(SECRET_KEY.encode('utf-8'), f"{header_b64}.{payload_b64}".encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature_raw).decode('utf-8').rstrip('=')

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_jwt_token(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), f"{header_b64}.{payload_b64}".encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Add padding back
        padded_payload = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode('utf-8')).decode('utf-8'))

        if payload.get("exp") and time.time() > payload["exp"]:
            return None

        return payload
    except Exception:
        return None

class AuthService:
    @staticmethod
    def register_user(email: str, password: str, name: str = "Adventurer") -> UserResponse:
        email = email.lower().strip()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="An account with this email already exists.")

        password_hash = hash_password(password)
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO users (email, password_hash, name, tier, is_guest, created_at, updated_at)
            VALUES (?, ?, ?, 'free', 0, ?, ?)
        """, (email, password_hash, name, now, now))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Seed initial facts and profile for new user
        seed_starter_data_for_user(user_id)

        return AuthService.get_user_by_id(user_id)

    @staticmethod
    def authenticate_user(email: str, password: str) -> UserResponse:
        email = email.lower().strip()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return AuthService.get_user_by_id(user["id"])

    @staticmethod
    def get_or_create_guest() -> UserResponse:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_guest = 1 ORDER BY id ASC LIMIT 1")
        guest = cursor.fetchone()

        if not guest:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO users (email, password_hash, name, tier, is_guest, created_at, updated_at)
                VALUES ('guest@stumpy.ai', 'guest_mode_unhashed', 'Guest Explorer', 'free', 1, ?, ?)
            """, (now, now))
            guest_id = cursor.lastrowid
            conn.commit()
            seed_starter_data_for_user(guest_id)
        else:
            guest_id = guest["id"]

        conn.close()
        return AuthService.get_user_by_id(guest_id)

    @staticmethod
    def get_user_by_id(user_id: int) -> UserResponse:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found.")

        # Count user's current resources
        cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,))
        memories_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM knowledge_notes WHERE user_id = ?", (user_id,))
        notes_count = cursor.fetchone()[0]

        # Count quizzes taken today
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM quizzes WHERE user_id = ? AND created_at LIKE ?", (user_id, f"{today_str}%"))
        quizzes_today = cursor.fetchone()[0]

        conn.close()

        tier = user["tier"] or "free"
        memory_limit = 999999 if tier == "pro" else 50
        quiz_daily_limit = 999999 if tier == "pro" else 5
        note_limit = 999999 if tier == "pro" else 10

        return UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            tier=tier,
            is_guest=bool(user["is_guest"]),
            memories_count=memories_count,
            memory_limit=memory_limit,
            quizzes_today=quizzes_today,
            quiz_daily_limit=quiz_daily_limit,
            notes_count=notes_count,
            note_limit=note_limit,
            created_at=user["created_at"]
        )

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserResponse:
    if not credentials:
        # Fallback to guest user for instant public trial
        return AuthService.get_or_create_guest()

    token = credentials.credentials
    payload = decode_jwt_token(token)
    if not payload or "sub" not in payload:
        return AuthService.get_or_create_guest()

    user_id = payload["sub"]
    try:
        return AuthService.get_user_by_id(user_id)
    except HTTPException:
        return AuthService.get_or_create_guest()
