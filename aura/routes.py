import json
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from aura.config import settings, BASE_DIR
from aura.models import (
    PinUpdateRequest,
    TimerSettingRequest,
    AdminActionRequest,
    AnswerSubmission,
    AdminPinChangeRequest,
    StageAuthRequest,
    ManualQuestionCreate,
    EmojiReaction,
    UnbanRequest,
    Question,
    QuestionOption,
    PlayerScoreAdjustRequest,
    QuizFolderCreate
)
from aura.game_manager import game_manager
from aura.gemini_service import gemini_service
from aura.firebase_service import get_firebase_web_config
from aura.security import security_service
from aura.export_service import generate_excel_report, generate_pdf_report

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Helper: Verify Admin PIN ---
def verify_admin_pin(admin_pin: str) -> bool:
    clean_input = str(admin_pin or "").strip()
    clean_expected = str(settings.ADMIN_PIN or "").strip()
    if not clean_input or clean_input != clean_expected:
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
    pin = str(payload.stage_pin or "").strip()
    expected_stage = str(settings.STAGE_PIN or "").strip()
    expected_admin = str(settings.ADMIN_PIN or "").strip()
    if pin and (pin == expected_stage or pin == expected_admin):
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
@router.post("/api/reaction")
async def post_reaction(payload: EmojiReaction):
    res = await game_manager.post_reaction(payload.emoji, payload.sender or "İzleyici")
    return {"success": True, "reaction": res}

@router.post("/api/player/join")
async def player_join(payload: Dict[str, Any]):
    pin = str(payload.get("room_pin", "")).strip()
    name = str(payload.get("name", "")).strip()
    school = str(payload.get("school", "Halil İnalcık Anadolu Lisesi")).strip()
    avatar = str(payload.get("avatar", "🐼")).strip()
    player_id = str(payload.get("player_id", "")).strip()
    client_id = str(payload.get("client_id", player_id or name)).strip()

    if not pin or pin != game_manager.room_pin:
        raise HTTPException(status_code=400, detail="Geçersiz veya hatalı Oda PIN kodu!")

    # Güvenlik & Doğrulama: Harf Kuralı ve Argo/Siyasi İsim Filtresi (3 Hak Ban Kuralı)
    identifier = client_id or player_id or name
    is_valid, error_msg, meta = security_service.validate_name(name, identifier)
    if not is_valid:
        status_code = 403 if meta.get("banned") else 400
        raise HTTPException(status_code=status_code, detail=error_msg)

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

@router.get("/api/player/rank/{player_id}")
async def get_player_rank(player_id: str):
    rank_info = game_manager.get_player_rank(player_id)
    if not rank_info:
        raise HTTPException(status_code=404, detail="Oyuncu bulunamadı")
    return rank_info

# --- Admin API Routes ---
@router.post("/api/admin/verify")
async def admin_verify(payload: Dict[str, Any]):
    pin = str(payload.get("admin_pin", "")).strip()
    expected = str(settings.ADMIN_PIN or "").strip()
    if pin and pin == expected:
        return {"success": True, "message": "Yetkilendirme başarılı"}
    raise HTTPException(status_code=403, detail="Hatalı Admin PIN!")

@router.post("/api/admin/change-pin")
async def admin_change_pin(payload: AdminPinChangeRequest):
    current = str(payload.current_pin or "").strip()
    expected = str(settings.ADMIN_PIN or "").strip()
    if current != expected:
        raise HTTPException(status_code=403, detail="Mevcut Admin PIN hatalı!")
    new_pin = str(payload.new_pin or "").strip()
    if len(new_pin) < 4:
        raise HTTPException(status_code=400, detail="Yeni PIN en az 4 karakter olmalıdır!")
    settings.set_admin_pin(new_pin)
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
    q_dur = payload.question_duration or payload.duration or 15
    t_delay = payload.transition_delay or 5
    await game_manager.set_timer_settings(
        question_duration=q_dur,
        transition_delay=t_delay,
        auto_mode=payload.auto_mode
    )
    return {
        "success": True,
        "question_duration": game_manager.duration,
        "transition_delay": game_manager.transition_delay,
        "auto_mode": game_manager.auto_mode
    }

# --- Export Raporları (Excel & PDF) ---
@router.get("/api/admin/export/excel")
async def export_excel(admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    players = game_manager.get_leaderboard(limit=200)
    data = generate_excel_report(players)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=AI_ERA_Zirvesi_Sonuclar.xlsx"}
    )

@router.get("/api/admin/export/pdf")
async def export_pdf(admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    players = game_manager.get_leaderboard(limit=200)
    data = generate_pdf_report(players)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=AI_ERA_Zirvesi_Sonuc_Raporu.pdf"}
    )

# --- Oyuncu Puan Yönetimi (+ ve - Butonları) (Requirement 7) ---
@router.post("/api/admin/players/score")
async def admin_adjust_player_score(payload: PlayerScoreAdjustRequest):
    verify_admin_pin(payload.admin_pin)
    delta = payload.get_delta()
    player = await game_manager.adjust_player_score(payload.player_id, delta)
    if not player:
        raise HTTPException(status_code=404, detail="Oyuncu bulunamadı")
    return {"success": True, "new_score": player.score, "player": player.model_dump()}

# --- Quiz Klasörleri Yönetimi (Requirement 8) ---
@router.get("/api/admin/folders")
async def admin_get_folders(admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    return {
        "folders": game_manager.get_folders_list(),
        "active_folder_id": game_manager.active_folder_id
    }

@router.post("/api/admin/folders")
async def admin_create_folder(payload: QuizFolderCreate):
    verify_admin_pin(payload.admin_pin)
    title = payload.get_title()
    folder = await game_manager.create_folder(title, payload.description or "")
    return {"success": True, "folder": folder.model_dump()}

@router.delete("/api/admin/folders/{folder_id}")
async def admin_delete_folder(folder_id: str, admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    deleted = await game_manager.delete_folder(folder_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Varsayılan klasör silinemez veya klasör bulunamadı")
    return {"success": True}

@router.post("/api/admin/folders/{folder_id}/activate")
async def admin_activate_folder(folder_id: str, payload: Dict[str, str]):
    verify_admin_pin(payload.get("admin_pin", ""))
    activated = await game_manager.activate_folder(folder_id)
    if not activated:
        raise HTTPException(status_code=404, detail="Klasör bulunamadı")
    return {"success": True, "active_folder_id": folder_id}

# --- Quizlerim (Manuel Soru Yönetimi) ---
@router.post("/api/admin/questions/manual")
async def add_manual_question(payload: ManualQuestionCreate):
    verify_admin_pin(payload.admin_pin)
    new_q = Question(
        id=len(game_manager.questions) + 1,
        question=payload.question.strip(),
        options=payload.options,
        correct=payload.correct,
        explanation=payload.explanation.strip(),
        duration=payload.duration,
        difficulty=payload.difficulty or "Orta",
        folder_id=payload.folder_id or game_manager.active_folder_id
    )
    try:
        added = await game_manager.add_manual_question(new_q)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "question": added.model_dump(), "total": len(game_manager.questions)}

@router.delete("/api/admin/questions/{q_id}")
async def delete_question(q_id: int, admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    success = await game_manager.delete_question(q_id)
    if not success:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    return {"success": True, "total": len(game_manager.questions)}

# --- Ban Yönetimi ---
@router.get("/api/admin/banned")
async def get_banned_users(admin_pin: str = ""):
    verify_admin_pin(admin_pin)
    return {"banned_users": security_service.get_banned_list()}

@router.post("/api/admin/unban")
async def unban_user(payload: UnbanRequest):
    verify_admin_pin(payload.admin_pin)
    target_id = payload.get_target_id()
    res = security_service.unban_user(target_id)
    return {"success": res, "message": f"{target_id} kullanıcısının banı kaldırıldı"}

# --- Yapay Zeka Soru Üretici (Sınırlar: Tek seferde maks 50, toplam maks 60) (Requirement 9) ---
@router.post("/api/admin/generate-questions")
async def admin_generate_questions(payload: Dict[str, Any]):
    verify_admin_pin(payload.get("admin_pin", ""))
    count = int(payload.get("count", 30))

    # Single generation limit: Max 50 questions
    if count > 50:
        raise HTTPException(status_code=400, detail="Tek seferde maksimum 50 soru üretilebilir!")

    # Total questions limit: Max 60 questions
    current_total = len(game_manager.questions)
    folder_id = payload.get("folder_id", game_manager.active_folder_id)
    if count > 60:
        raise HTTPException(
            status_code=400,
            detail=f"Sistemde toplam soru sınırı maksimum 60 sorudur!"
        )

    difficulties = payload.get("difficulties")
    questions = await gemini_service.generate_questions_with_gemini(
        count=count,
        difficulties=difficulties,
        folder_id=folder_id
    )

    try:
        await game_manager.set_questions(questions, folder_id=folder_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    folder_name = "Aktif Klasör"
    if folder_id in game_manager.folders:
        folder_name = game_manager.folders[folder_id].title

    return {
        "success": True,
        "count": len(questions),
        "total_questions": len(game_manager.questions),
        "folder_id": folder_id,
        "folder_name": folder_name,
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
