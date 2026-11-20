import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from aura.config import settings
from aura.models import Question, Player, GameState
from aura.gemini_service import gemini_service
from aura.firebase_service import sync_game_state_to_firestore, sync_player_to_firestore

logger = logging.getLogger("aura.game")

class GameManager:
    def __init__(self):
        self.room_pin: str = settings.DEFAULT_ROOM_PIN
        self.status: str = "LOBBY" # LOBBY, QUESTION, REVEAL, LEADERBOARD, PODIUM
        self.current_question_index: int = 0
        self.questions: List[Question] = gemini_service.get_default_questions()
        self.players: Dict[str, Player] = {}
        self.answer_stats: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        self.auto_mode: bool = False
        self.duration: int = 15 # 5, 10, or 15 seconds
        self.timer_remaining: int = 15
        self.question_start_timestamp: float = 0
        self._timer_task: Optional[asyncio.Task] = None
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    def get_current_question(self) -> Optional[Question]:
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    def get_public_state(self, include_correct: bool = False) -> Dict[str, Any]:
        """
        Returns the game state. Redacts the correct option during QUESTION state
        unless include_correct is True (for Admin or after REVEAL).
        """
        curr_q = self.get_current_question()
        q_dict = None
        if curr_q:
            q_dict = {
                "id": curr_q.id,
                "question": curr_q.question,
                "options": curr_q.options.model_dump(),
                "duration": self.duration
            }
            if include_correct or self.status in ("REVEAL", "LEADERBOARD", "PODIUM"):
                q_dict["correct"] = curr_q.correct
                q_dict["explanation"] = curr_q.explanation

        # Calculate answers count for current question
        answers_count = sum(self.answer_stats.values())

        return {
            "room_pin": self.room_pin,
            "status": self.status,
            "current_question_index": self.current_question_index,
            "total_questions": len(self.questions),
            "auto_mode": self.auto_mode,
            "duration": self.duration,
            "timer_remaining": self.timer_remaining,
            "question_start_timestamp": self.question_start_timestamp,
            "current_question": q_dict,
            "participants_count": len(self.players),
            "answers_count": answers_count,
            "answer_stats": self.answer_stats,
            "updated_at": time.time()
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (p.score, -p.joined_at),
            reverse=True
        )
        return [
            {
                "id": p.id,
                "name": p.name,
                "school": p.school,
                "avatar": p.avatar,
                "score": p.score,
                "streak": p.streak,
                "rank": idx + 1
            }
            for idx, p in enumerate(sorted_players[:limit])
        ]

    def get_podium(self) -> Dict[str, Any]:
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (p.score, -p.joined_at),
            reverse=True
        )
        first = sorted_players[0].model_dump() if len(sorted_players) > 0 else None
        second = sorted_players[1].model_dump() if len(sorted_players) > 1 else None
        third = sorted_players[2].model_dump() if len(sorted_players) > 2 else None
        return {
            "first": first,
            "second": second,
            "third": third,
            "total_players": len(sorted_players)
        }

    async def broadcast_state(self):
        """Notifies all connected SSE queues and syncs with Firestore"""
        state = self.get_public_state()
        
        # Async Firestore sync
        asyncio.create_task(sync_game_state_to_firestore(self.room_pin, state))

        # Push to in-memory SSE subscribers
        dead_queues = []
        for q in self._subscribers:
            try:
                q.put_nowait(state)
            except asyncio.QueueFull:
                dead_queues.append(q)
            except Exception:
                dead_queues.append(q)
        for dq in dead_queues:
            if dq in self._subscribers:
                self._subscribers.remove(dq)

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=20)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)

    def _cancel_timer(self):
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self._timer_task = None

    async def update_room_pin(self, new_pin: str) -> str:
        async with self._lock:
            self.room_pin = new_pin.strip()
            logger.info(f"Room PIN updated to: {self.room_pin}")
            await self.broadcast_state()
            return self.room_pin

    async def set_questions(self, questions: List[Question]):
        async with self._lock:
            self.questions = questions
            self.current_question_index = 0
            self.status = "LOBBY"
            self._reset_answers()
            await self.broadcast_state()

    def _reset_answers(self):
        self.answer_stats = {"A": 0, "B": 0, "C": 0, "D": 0}
        for p in self.players.values():
            p.last_answer = None
            p.answered_at = None
            p.is_correct = None

    async def join_player(self, player_id: str, name: str, school: str, avatar: str) -> Player:
        async with self._lock:
            player = Player(
                id=player_id,
                name=name.strip()[:24],
                school=(school.strip() or "Bağımsız")[:32],
                avatar=avatar or "🚀",
                score=0,
                streak=0,
                joined_at=time.time()
            )
            self.players[player_id] = player
            asyncio.create_task(sync_player_to_firestore(self.room_pin, player_id, player.model_dump()))
            await self.broadcast_state()
            return player

    async def leave_player(self, player_id: str) -> bool:
        async with self._lock:
            if player_id in self.players:
                del self.players[player_id]
                await self.broadcast_state()
                return True
            return False

    async def start_game(self):
        async with self._lock:
            self._cancel_timer()
            self.status = "QUESTION"
            self.current_question_index = 0
            self.timer_remaining = self.duration
            self.question_start_timestamp = time.time()
            self._reset_answers()
            await self.broadcast_state()
            self._start_countdown()

    async def next_question(self):
        async with self._lock:
            self._cancel_timer()
            if self.current_question_index + 1 < len(self.questions):
                self.current_question_index += 1
                self.status = "QUESTION"
                self.timer_remaining = self.duration
                self.question_start_timestamp = time.time()
                self._reset_answers()
                await self.broadcast_state()
                self._start_countdown()
            else:
                self.status = "PODIUM"
                await self.broadcast_state()

    async def reveal_answer(self):
        async with self._lock:
            self._cancel_timer()
            self.status = "REVEAL"
            await self.broadcast_state()
            if self.auto_mode:
                self._schedule_auto_transition("LEADERBOARD", delay_seconds=4)

    async def show_leaderboard(self):
        async with self._lock:
            self._cancel_timer()
            self.status = "LEADERBOARD"
            await self.broadcast_state()
            if self.auto_mode:
                self._schedule_auto_transition("NEXT_QUESTION", delay_seconds=5)

    async def finish_podium(self):
        async with self._lock:
            self._cancel_timer()
            self.status = "PODIUM"
            await self.broadcast_state()

    async def reset_room(self):
        async with self._lock:
            self._cancel_timer()
            self.status = "LOBBY"
            self.current_question_index = 0
            self.players.clear()
            self._reset_answers()
            await self.broadcast_state()

    async def set_timer_settings(self, duration: int, auto_mode: bool):
        async with self._lock:
            if duration in (5, 10, 15):
                self.duration = duration
                if self.status == "QUESTION":
                    self.timer_remaining = min(self.timer_remaining, self.duration)
            self.auto_mode = auto_mode
            await self.broadcast_state()

    async def submit_answer(self, player_id: str, question_id: int, choice: str) -> Dict[str, Any]:
        async with self._lock:
            if self.status != "QUESTION":
                return {"success": False, "error": "Soru aşamasında değil"}

            curr_q = self.get_current_question()
            if not curr_q or curr_q.id != question_id:
                return {"success": False, "error": "Geçersiz soru"}

            player = self.players.get(player_id)
            if not player:
                return {"success": False, "error": "Oyuncu bulunamadı"}

            if player.last_answer is not None:
                return {"success": False, "error": "Zaten cevap verdiniz"}

            now = time.time()
            elapsed = max(0.1, now - self.question_start_timestamp)
            time_ratio = max(0.0, 1.0 - (elapsed / float(self.duration)))

            is_correct = (choice == curr_q.correct)
            points = 0
            if is_correct:
                # Kahoot scoring algorithm: base 500 + up to 500 points for speed
                points = int(500 + (500 * time_ratio))
                player.score += points
                player.streak += 1
            else:
                player.streak = 0

            player.last_answer = choice
            player.answered_at = now
            player.is_correct = is_correct

            if choice in self.answer_stats:
                self.answer_stats[choice] += 1

            # Check if all players answered
            answers_count = sum(self.answer_stats.values())
            all_answered = (len(self.players) > 0 and answers_count >= len(self.players))

            await self.broadcast_state()

            if all_answered and self.status == "QUESTION":
                # Automatically reveal when everyone has answered!
                asyncio.create_task(self.reveal_answer())

            return {
                "success": True,
                "is_correct": is_correct,
                "points_earned": points,
                "current_score": player.score,
                "streak": player.streak
            }

    def _start_countdown(self):
        """Starts the timer countdown in background"""
        self._cancel_timer()

        async def countdown():
            try:
                while self.timer_remaining > 0 and self.status == "QUESTION":
                    await asyncio.sleep(1)
                    if self.status != "QUESTION":
                        break
                    self.timer_remaining -= 1
                    await self.broadcast_state()

                if self.timer_remaining <= 0 and self.status == "QUESTION":
                    await self.reveal_answer()
            except asyncio.CancelledError:
                pass

        self._timer_task = asyncio.create_task(countdown())

    def _schedule_auto_transition(self, target: str, delay_seconds: int):
        """Schedules auto step in Auto Mode without overlapping"""
        async def auto_step():
            try:
                await asyncio.sleep(delay_seconds)
                if not self.auto_mode:
                    return
                if target == "LEADERBOARD" and self.status == "REVEAL":
                    await self.show_leaderboard()
                elif target == "NEXT_QUESTION" and self.status == "LEADERBOARD":
                    await self.next_question()
            except asyncio.CancelledError:
                pass

        asyncio.create_task(auto_step())

game_manager = GameManager()
