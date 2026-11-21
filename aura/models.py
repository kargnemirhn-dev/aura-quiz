from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
import time

class QuestionOption(BaseModel):
    A: str
    B: str
    C: str
    D: str

class Question(BaseModel):
    id: int
    question: str
    options: QuestionOption
    correct: Literal["A", "B", "C", "D"]
    explanation: Optional[str] = ""
    duration: int = 15
    difficulty: Optional[str] = "Orta" # Çok Kolay, Kolay, Orta, Zor
    folder_id: Optional[str] = "default"

class QuizFolder(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    created_at: float = Field(default_factory=time.time)
    questions: List[Question] = Field(default_factory=list)

class QuizFolderCreate(BaseModel):
    admin_pin: str
    title: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = ""

    def get_title(self) -> str:
        return self.title or self.name or "Yeni Quiz Klasörü"

class Player(BaseModel):
    id: str
    name: str
    school: str = "Diğer"
    avatar: str = "🚀"
    score: int = 0
    streak: int = 0
    last_answer: Optional[str] = None
    answered_at: Optional[float] = None
    is_correct: Optional[bool] = None
    joined_at: float = Field(default_factory=time.time)

class PlayerScoreAdjustRequest(BaseModel):
    admin_pin: str
    player_id: str
    score_delta: Optional[int] = None
    delta: Optional[int] = None

    def get_delta(self) -> int:
        if self.score_delta is not None:
            return self.score_delta
        if self.delta is not None:
            return self.delta
        return 0

class AnswerSubmission(BaseModel):
    player_id: str
    question_id: int
    choice: Literal["A", "B", "C", "D"]
    response_time_ms: int = 0

class PinUpdateRequest(BaseModel):
    admin_pin: str
    new_room_pin: str

class AdminPinChangeRequest(BaseModel):
    current_pin: str
    new_pin: str

class StageAuthRequest(BaseModel):
    stage_pin: str

class TimerSettingRequest(BaseModel):
    admin_pin: str
    duration: Optional[int] = None # legacy compatibility
    question_duration: Optional[int] = 15 # 5, 10, 15, 20, 30s
    transition_delay: Optional[int] = 5 # 3, 5, 10s
    auto_mode: bool = False

class ManualQuestionCreate(BaseModel):
    admin_pin: str
    question: str
    options: QuestionOption
    correct: Literal["A", "B", "C", "D"]
    explanation: Optional[str] = ""
    duration: int = 15
    difficulty: Optional[str] = "Orta"
    folder_id: Optional[str] = "default"

class DifficultyCounts(BaseModel):
    cok_kolay: int = 0
    kolay: int = 0
    orta: int = 0
    zor: int = 0

class AIQuestionGenerateRequest(BaseModel):
    admin_pin: str
    count: int = Field(default=30, ge=1, le=50) # Maximum 50 questions per generation
    difficulties: Optional[DifficultyCounts] = None
    folder_id: Optional[str] = "default"

class EmojiReaction(BaseModel):
    emoji: str
    sender: Optional[str] = "İzleyici"
    room_pin: Optional[str] = ""

class UnbanRequest(BaseModel):
    admin_pin: str
    user_id: Optional[str] = None
    identifier: Optional[str] = None

    def get_target_id(self) -> str:
        return self.user_id or self.identifier or ""

class ThemeUpdateRequest(BaseModel):
    admin_pin: str
    theme: Literal["default", "cyberpunk", "dark-neon", "corporate"] = "default"

class AdminActionRequest(BaseModel):
    admin_pin: str
    action: Literal[
        "START_GAME",
        "NEXT_QUESTION",
        "REVEAL_ANSWER",
        "SHOW_LEADERBOARD",
        "FINISH_PODIUM",
        "RESET_ROOM",
        "SET_AUTO_MODE",
        "SET_DURATION",
        "SET_THEME"
    ]
    payload: Optional[Dict] = None

class GameState(BaseModel):
    room_pin: str
    status: Literal["LOBBY", "COUNTDOWN", "QUESTION", "REVEAL", "LEADERBOARD", "PODIUM"] = "LOBBY"
    current_question_index: int = 0
    total_questions: int = 30
    auto_mode: bool = False
    duration: int = 15 # Question duration
    transition_delay: int = 5 # Auto transition duration on leaderboard
    timer_remaining: int = 15
    leaderboard_countdown: int = 5
    countdown_remaining: int = 5
    countdown_start_timestamp: float = 0
    question_start_timestamp: float = 0
    theme: str = "default"
    schools_leaderboard: List[Dict[str, Any]] = Field(default_factory=list)
    current_question: Optional[Dict] = None
    participants_count: int = 0
    answers_count: int = 0
    answer_stats: Dict[str, int] = Field(default_factory=lambda: {"A": 0, "B": 0, "C": 0, "D": 0})
    last_reaction: Optional[Dict] = None
    active_folder_id: Optional[str] = "default"
    updated_at: float = Field(default_factory=time.time)
