from pydantic import BaseModel
from typing import List, Optional

class SkillItem(BaseModel):
    id: Optional[int] = None
    name: str
    category: str = "Programming"
    mastery_level: float = 10.0
    target_level: float = 100.0
    total_quizzes_taken: int = 0
    correct_answers: int = 0
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SkillCreate(BaseModel):
    name: str
    category: str = "Programming"
    notes: str = ""

class QuizOption(BaseModel):
    index: int
    text: str

class QuizQuestion(BaseModel):
    id: Optional[int] = None
    skill_id: int
    skill_name: Optional[str] = None
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str
    difficulty: str = "intermediate"

class QuizSubmit(BaseModel):
    quiz_id: int
    selected_option_index: int

class QuizResult(BaseModel):
    quiz_id: int
    is_correct: bool
    correct_option_index: int
    explanation: str
    new_mastery_level: float
    streak_bonus: Optional[str] = None
