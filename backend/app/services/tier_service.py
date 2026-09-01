from fastapi import HTTPException
from app.models.user import UserResponse

class TierService:
    @staticmethod
    def check_memory_quota(user: UserResponse):
        if user.tier == "pro":
            return True
        if user.memories_count >= user.memory_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Free Tier Memory Limit Reached ({user.memories_count}/{user.memory_limit} memories). Upgrade to Stumpy Pro for unlimited persistent memories!"
            )
        return True

    @staticmethod
    def check_quiz_quota(user: UserResponse):
        if user.tier == "pro":
            return True
        if user.quizzes_today >= user.quiz_daily_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Daily Quiz Limit Reached ({user.quizzes_today}/{user.quiz_daily_limit} today). Upgrade to Stumpy Pro for unlimited daily skill quizzes!"
            )
        return True

    @staticmethod
    def check_note_quota(user: UserResponse):
        if user.tier == "pro":
            return True
        if user.notes_count >= user.note_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Second Brain Note Limit Reached ({user.notes_count}/{user.note_limit} notes). Upgrade to Stumpy Pro for unlimited knowledge storage!"
            )
        return True

    @staticmethod
    def check_model_access(user: UserResponse, provider: str):
        if provider in ("gemini", "openai") and user.tier != "pro":
            # For public SaaS, direct premium cloud model access is reserved for Pro users
            # (or users with personal keys configured)
            pass
        return True
