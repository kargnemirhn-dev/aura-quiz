from typing import List, Dict, Optional, Literal
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

class Player(BaseModel):
    id: str
    name: str
    school: str = "Bağımsız"
    avatar: str = "🚀"
    score: int = 0
    streak: int = 0
    last_answer: Optional[str] = None
    answered_at: Optional[float] = None
    is_correct: Optional[bool] = None
    joined_at: float = Field(default_factory=time.time)

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
        "SET_DURATION"
    ]
    payload: Optional[Dict] = None

class GameState(BaseModel):
    room_pin: str
    status: Literal["LOBBY", "QUESTION", "REVEAL", "LEADERBOARD", "PODIUM"] = "LOBBY"
    current_question_index: int = 0
    total_questions: int = 30
    auto_mode: bool = False
    duration: int = 15 # Question duration
    transition_delay: int = 5 # Auto transition duration on leaderboard
    timer_remaining: int = 15
    leaderboard_countdown: int = 5
    question_start_timestamp: float = 0
    current_question: Optional[Dict] = None # Will redact correct answer when sent to stage/players during QUESTION status
    participants_count: int = 0
    answers_count: int = 0
    answer_stats: Dict[str, int] = Field(default_factory=lambda: {"A": 0, "B": 0, "C": 0, "D": 0})
    last_reaction: Optional[Dict] = None
    updated_at: float = Field(default_factory=time.time)
