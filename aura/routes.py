import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from aura.config import settings, BASE_DIR
from aura.models import (
    PinUpdateRequest,
    TimerSettingRequest,
    AdminActionRequest,
    AnswerSubmission,
    AdminPinChangeRequest,
    StageAuthRequest
)
from aura.game_manager import game_manager
from aura.gemini_service import gemini_service
from aura.firebase_service import get_firebase_web_config

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Helper: Verify Admin PIN ---
def verify_admin_pin(admin_pin: str) -> bool:
    if not admin_pin or admin_pin != settings.ADMIN_PIN:
        raise HTTPException(status_code=403, detail="Geçersiz Admin PIN kodu")
    return True

# --- HTML Page Routes ---
@router.get("/", response_class=HTMLResponse)
async def page_portal(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": settings.PROJECT_NAME,
            "subtitle": settings.PROJECT_SUBTITLE,
            "room_pin": game_manager.room_pin,
            "firebase_config": get_firebase_web_config()
        }
    )

@router.get("/stage", response_class=HTMLResponse)
async def page_stage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="stage.html",
        context={
            "title": settings.PROJECT_NAME,
            "subtitle": settings.PROJECT_SUBTITLE,
            "room_pin": game_manager.room_pin,
            "firebase_config": get_firebase_web_config()
        }
    )

@router.get("/play", response_class=HTMLResponse)
async def page_play(request: Request, pin: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="play.html",
        context={
            "title": settings.PROJECT_NAME,
            "subtitle": settings.PROJECT_SUBTITLE,
            "preset_pin": pin or game_manager.room_pin,
            "firebase_config": get_firebase_web_config()
        }
    )

@router.get("/admin", response_class=HTMLResponse)
async def page_admin(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "title": settings.PROJECT_NAME,
            "subtitle": settings.PROJECT_SUBTITLE,
            "room_pin": game_manager.room_pin,
            "firebase_config": get_firebase_web_config()
        }
    )

# --- Real-Time SSE Stream ---
@router.get("/api/events")
async def events_stream(request: Request):
    async def event_generator():
        q = game_manager.subscribe()
        try:
            # Yield initial state immediately
            initial_state = game_manager.get_public_state()
            yield f"data: {json.dumps(initial_state)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    state = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(state)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield ": ping\n\n"
        finally:
            game_manager.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- Public API Routes ---
@router.post("/api/stage/verify")
async def stage_verify(payload: StageAuthRequest):
    pin = payload.stage_pin.strip()
    if pin == settings.STAGE_PIN or pin == settings.ADMIN_PIN:
        return {"success": True, "message": "Sahne yetkilendirmesi başarılı"}
    raise HTTPException(status_code=403, detail="Hatalı Sahne PIN kodu!")

@router.get("/api/state")
async def get_state():
    return game_manager.get_public_state()

@router.get("/api/leaderboard")
async def get_leaderboard(limit: int = 10):
    return game_manager.get_leaderboard(limit=limit)

@router.get("/api/podium")
async def get_podium():
    return game_manager.get_podium()

@router.get("/api/firebase-config")
async def get_fb_config():
    return get_firebase_web_config()

# --- Player API Routes ---
@router.post("/api/player/join")
async def player_join(payload: Dict[str, Any]):
    pin = str(payload.get("room_pin", "")).strip()
    name = str(payload.get("name", "")).strip()
    school = str(payload.get("school", "Bağımsız")).strip()
    avatar = str(payload.get("avatar", "🚀")).strip()
    player_id = str(payload.get("player_id", "")).strip()

    if not pin or pin != game_manager.room_pin:
        raise HTTPException(status_code=400, detail="Geçersiz veya hatalı Oda PIN kodu!")

    if not name:
        raise HTTPException(status_code=400, detail="Lütfen bir isim giriniz!")

    if not player_id:
        import uuid
        player_id = str(uuid.uuid4())

    player = await game_manager.join_player(player_id, name, school, avatar)
    return {
        "success": True,
        "player": player.model_dump(),
        "room_pin": game_manager.room_pin
    }

@router.post("/api/player/leave")
async def player_leave(payload: Dict[str, Any]):
    player_id = str(payload.get("player_id", "")).strip()
    left = await game_manager.leave_player(player_id)
    return {"success": left}

@router.post("/api/player/answer")
async def player_answer(payload: AnswerSubmission):
    result = await game_manager.submit_answer(
        player_id=payload.player_id,
        question_id=payload.question_id,
        choice=payload.choice
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Hata oluştu"))
    return result

# --- Admin API Routes ---
@router.post("/api/admin/verify")
async def admin_verify(payload: Dict[str, str]):
    pin = payload.get("admin_pin", "")
    if pin == settings.ADMIN_PIN:
        return {"success": True, "message": "Yetkilendirme başarılı"}
    raise HTTPException(status_code=403, detail="Hatalı Admin PIN!")

@router.post("/api/admin/change-pin")
async def admin_change_pin(payload: AdminPinChangeRequest):
    if payload.current_pin.strip() != settings.ADMIN_PIN:
        raise HTTPException(status_code=403, detail="Mevcut Admin PIN hatalı!")
    if len(payload.new_pin.strip()) < 4:
        raise HTTPException(status_code=400, detail="Yeni PIN en az 4 karakter olmalıdır!")
    settings.set_admin_pin(payload.new_pin.strip())
    return {"success": True, "message": "Admin PIN başarıyla güncellendi!"}

@router.post("/api/admin/random-pin")
async def admin_random_pin(payload: Dict[str, str]):
    verify_admin_pin(payload.get("admin_pin", ""))
    from aura.game_manager import generate_random_6digit_pin
    new_pin = generate_random_6digit_pin()
    await game_manager.update_room_pin(new_pin)
    return {"success": True, "room_pin": new_pin}

@router.post("/api/admin/pin")
async def admin_update_pin(payload: PinUpdateRequest):
    verify_admin_pin(payload.admin_pin)
    if not payload.new_room_pin or len(payload.new_room_pin.strip()) < 3:
        raise HTTPException(status_code=400, detail="Oda PIN en az 3 haneli olmalıdır.")
    new_pin = await game_manager.update_room_pin(payload.new_room_pin.strip())
    return {"success": True, "room_pin": new_pin}

@router.post("/api/admin/timer")
async def admin_set_timer(payload: TimerSettingRequest):
    verify_admin_pin(payload.admin_pin)
    if payload.duration not in (5, 10, 15):
        raise HTTPException(status_code=400, detail="Süre sadece 5, 10 veya 15 saniye olabilir.")
    await game_manager.set_timer_settings(payload.duration, payload.auto_mode)
    return {"success": True, "duration": payload.duration, "auto_mode": payload.auto_mode}

@router.post("/api/admin/generate-questions")
async def admin_generate_questions(payload: Dict[str, Any]):
    admin_pin = payload.get("admin_pin", "")
    verify_admin_pin(admin_pin)
    count = int(payload.get("count", 30))
    questions = await gemini_service.generate_questions_with_gemini(count=count)
    await game_manager.set_questions(questions)
    return {
        "success": True,
        "count": len(questions),
        "questions": [q.model_dump() for q in questions]
    }

@router.get("/api/admin/questions")
async def admin_get_questions(admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    return {
        "count": len(game_manager.questions),
        "questions": [q.model_dump() for q in game_manager.questions]
    }

@router.post("/api/admin/action")
async def admin_action(payload: AdminActionRequest):
    verify_admin_pin(payload.admin_pin)
    action = payload.action

    if action == "START_GAME":
        await game_manager.start_game()
    elif action == "NEXT_QUESTION":
        await game_manager.next_question()
    elif action == "REVEAL_ANSWER":
        await game_manager.reveal_answer()
    elif action == "SHOW_LEADERBOARD":
        await game_manager.show_leaderboard()
    elif action == "FINISH_PODIUM":
        await game_manager.finish_podium()
    elif action == "RESET_ROOM":
        await game_manager.reset_room()
    elif action == "SET_AUTO_MODE":
        auto = bool(payload.payload.get("auto_mode", False)) if payload.payload else False
        await game_manager.set_timer_settings(game_manager.duration, auto)
    elif action == "SET_DURATION":
        duration = int(payload.payload.get("duration", 15)) if payload.payload else 15
        await game_manager.set_timer_settings(duration, game_manager.auto_mode)
    else:
        raise HTTPException(status_code=400, detail=f"Bilinmeyen aksiyon: {action}")

    return {"success": True, "status": game_manager.status}
