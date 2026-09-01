from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.models.skill import SkillItem, SkillCreate, QuizQuestion, QuizSubmit, QuizResult
from app.models.user import UserResponse
from app.services.skill_service import SkillService
from app.services.auth_service import get_current_user
from app.services.tier_service import TierService
from app.database import get_db_connection

router = APIRouter(prefix="/api/skills", tags=["Skills & Quizzes"])

@router.get("", response_model=List[SkillItem])
def list_skills(user: UserResponse = Depends(get_current_user)):
    return SkillService.get_all_skills(user_id=user.id)

@router.post("", response_model=SkillItem)
def create_skill(data: SkillCreate, user: UserResponse = Depends(get_current_user)):
    return SkillService.create_skill(name=data.name, category=data.category, notes=data.notes, user_id=user.id)

@router.get("/{skill_id}/quiz", response_model=QuizQuestion)
def get_quiz_question(skill_id: int, user: UserResponse = Depends(get_current_user)):
    # Check Free tier daily quiz quota
    TierService.check_quiz_quota(user)

    try:
        return SkillService.generate_quiz_for_skill(skill_id, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/quiz/submit", response_model=QuizResult)
def submit_quiz_answer(data: QuizSubmit, user: UserResponse = Depends(get_current_user)):
    try:
        return SkillService.submit_quiz_answer(data.quiz_id, data.selected_option_index, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{skill_id}")
def delete_skill(skill_id: int, user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quizzes WHERE skill_id = ? AND user_id = ?", (skill_id, user.id))
    cursor.execute("DELETE FROM skills WHERE id = ? AND user_id = ?", (skill_id, user.id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "success", "id": skill_id}
