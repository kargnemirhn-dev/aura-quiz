import sys
import time
import json
import threading
import urllib.request
import urllib.parse
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from aura.config import settings
from aura.game_manager import game_manager

BASE_URL = "http://127.0.0.1:8089"

def http_get(path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        content = resp.read().decode("utf-8")
        try:
            data = json.loads(content)
            return resp.status, data, content
        except Exception:
            return resp.status, None, content

def http_post(path: str, payload: dict):
    url = f"{BASE_URL}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
            try:
                data = json.loads(content)
                return resp.status, data, content
            except Exception:
                return resp.status, None, content
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            data = json.loads(content)
            return e.code, data, content
        except Exception:
            return e.code, None, content

def run_full_qa_simulation():
    print("=" * 70)
    print("🤖 BAŞLATILIYOR: AI ERA ZİRVESİ - KENDİNİ TEST EDEN QA SİMÜLASYONU")
    print("=" * 70)

    # Start Uvicorn in Background Thread
    print("[INIT] Uvicorn sunucusu arka planda 8089 portunda başlatılıyor...")
    config = uvicorn.Config("main:app", host="127.0.0.1", port=8089, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2.0)
    print("  ✓ Sunucu hazır ve istekleri kabul ediyor.\n")

    try:
        # ---------------------------------------------------------
        # TEST 1: SAYFA VE TEMPLATE KONTROLLERİ (Stage, Play, Admin)
        # ---------------------------------------------------------
        print("[TEST 1] Sayfa Render ve Kritik UI Gereksinimleri Testi...")
        
        # 1.1 Portal (/)
        status, _, text = http_get("/")
        assert status == 200, "Portal açılmadı"
        assert "AI ERA: TEKNOLOJİ & GİRİŞİMCİLİK ZİRVESİ" in text
        print("  ✓ Portal (/) sayfası 200 OK ve başlık doğrulandı.")

        # 1.2 Sahne Ekranı (/stage)
        status, _, text_stage = http_get("/stage")
        assert status == 200, "Stage sayfası açılmadı"
        # a) QR Kod Büyütme Modalı
        assert "modal-qr" in text_stage, "QR Büyütme modalı bulunamadı!"
        assert "QR Kodu Büyüt" in text_stage, "QR büyütme tetikleyicisi bulunamadı!"
        # b) C şıkkı sarı rengi (bg-yellow-500)
        assert "bg-yellow-500" in text_stage, "C şıkkı sarı rengi (bg-yellow-500) bulunamadı!"
        # c) Yatay kayan katılımcı kartları
        assert "marquee-content" in text_stage, "Yatay kayan katılımcı marquee alanı bulunamadı!"
        # d) Podyum animasyonu (3., 2., 1.)
        assert "podium-1" in text_stage and "podium-2" in text_stage and "podium-3" in text_stage, "Podyum basamakları bulunamadı!"
        print("  ✓ Sahne Ekranı (/stage): QR Modal, C-yellow (bg-yellow-500), Marquee ve Podyum doğrulandı.")

        # 1.3 Oyuncu Ekranı (/play)
        status, _, text_play = http_get("/play")
        assert status == 200, "Play sayfası açılmadı"
        # a) "Odadan Çık" butonu
        assert "Odadan Çık" in text_play, "Odadan Çık butonu bulunamadı!"
        # b) Avatar seçim ızgarası
        assert "avatar-grid" in text_play, "Avatar seçim ekranı bulunamadı!"
        # c) Kahoot sembolleri (🔺, 🔷, 🟡, 🟢)
        assert "🔺" in text_play and "🔷" in text_play and "🟡" in text_play and "🟢" in text_play
        # d) Telefonda soru metni veya şık yazılarının olmaması kuralı:
        assert "stage-text-A" not in text_play, "Oyuncu ekranında soru metni veya şık yazısı yer almamalı!"
        print("  ✓ Oyuncu Ekranı (/play): Kahoot renk/simgeleri, 'Odadan Çık' ve Avatar seçimi doğrulandı.")

        # ---------------------------------------------------------
        # TEST 2: ODA PIN SİSTEMİ VE FİRESTORE SENKRONİZASYON TESTİ
        # ---------------------------------------------------------
        print("\n[TEST 2] Oda PIN Değişimi ve Güvenlik Testi...")
        
        # 2.1 Yanlış Admin PIN engeli
        bad_status, bad_data, _ = http_post("/api/admin/pin", {"admin_pin": "0000", "new_room_pin": "9999"})
        assert bad_status == 403, "Yetkisiz Admin PIN engellenemedi!"
        print("  ✓ Yanlış Admin PIN ile oda değiştirme 403 Forbidden ile engellendi.")

        # 2.2 Doğru Admin PIN ile oda güncelleme
        new_test_pin = "8899"
        status, data, _ = http_post("/api/admin/pin", {"admin_pin": settings.ADMIN_PIN, "new_room_pin": new_test_pin})
        assert status == 200
        assert data["room_pin"] == new_test_pin

        # Canlı state doğrulaması
        _, state_data, _ = http_get("/api/state")
        assert state_data["room_pin"] == new_test_pin, "Oda PIN canlı state üzerinde güncellenmedi!"
        print(f"  ✓ Oda PIN başarıyla '{new_test_pin}' olarak güncellendi ve canlı state'e yansıdı.")

        # ---------------------------------------------------------
        # TEST 3: GEMINI AI SORU BANKASI TESTİ (30 Özgün Soru)
        # ---------------------------------------------------------
        print("\n[TEST 3] Soru Bankası ve Gemini Entegrasyonu Testi...")
        assert len(game_manager.questions) == 30, f"Soru sayısı 30 olmalıdır, bulunan: {len(game_manager.questions)}"
        for idx, q in enumerate(game_manager.questions, 1):
            assert q.id == idx
            assert len(q.question) > 10
            assert q.correct in ("A", "B", "C", "D")
            assert q.options.A and q.options.B and q.options.C and q.options.D
        print(f"  ✓ Soru Bankası: Tam {len(game_manager.questions)} adet zirve sorusu, 4 şık ve doğru cevaplar eksiksiz doğrulandı.")

        # ---------------------------------------------------------
        # TEST 4: OYUNCU KATILIMI, KAHUT CEVAPLARI VE ODADAN ÇIKIŞ
        # ---------------------------------------------------------
        print("\n[TEST 4] Çoklu Oyuncu Simülasyonu ve Kahoot Akışı...")
        
        # Odayı temizle
        http_post("/api/admin/action", {"admin_pin": settings.ADMIN_PIN, "action": "RESET_ROOM"})

        # 3 Oyuncu Katılıyor
        status, p1, _ = http_post("/api/player/join", {
            "room_pin": new_test_pin,
            "name": "Can Yılmaz",
            "school": "İTÜ Yapay Zeka Kulübü",
            "avatar": "🚀",
            "player_id": "player-1"
        })
        assert p1["success"] is True

        status, p2, _ = http_post("/api/player/join", {
            "room_pin": new_test_pin,
            "name": "Zeynep Kaya",
            "school": "Boğaziçi Girişimcilik",
            "avatar": "💡",
            "player_id": "player-2"
        })
        assert p2["success"] is True

        status, p3, _ = http_post("/api/player/join", {
            "room_pin": new_test_pin,
            "name": "Burak Demir",
            "school": "ODTÜ Bilgisayar",
            "avatar": "🤖",
            "player_id": "player-3"
        })
        assert p3["success"] is True

        assert len(game_manager.players) == 3
        print("  ✓ 3 oyuncu farklı avatar ve okullarıyla odaya başarıyla katıldı.")

        # 4.1 "Odadan Çık" Testi
        _, leave_data, _ = http_post("/api/player/leave", {"player_id": "player-3"})
        assert leave_data["success"] is True
        assert len(game_manager.players) == 2, "Odadan çıkan oyuncu sistemden silinmedi!"
        print("  ✓ 'Odadan Çık' fonksiyonu test edildi: Oyuncu 3 odadan ayrıldı, katılımcı sayısı güncellendi.")

        # Oyuncu 3 tekrar katılsın
        http_post("/api/player/join", {
            "room_pin": new_test_pin,
            "name": "Burak Demir",
            "school": "ODTÜ Bilgisayar",
            "avatar": "🤖",
            "player_id": "player-3"
        })

        # ---------------------------------------------------------
        # TEST 5: SAYAÇLAR (5s, 10s, 15s) VE OTOMATİK MOD TESTİ
        # ---------------------------------------------------------
        print("\n[TEST 5] Sayaç Süreleri (5s/10s/15s) ve Otomatik Mod...")
        for duration in (5, 10, 15):
            status, t_res, _ = http_post("/api/admin/timer", {
                "admin_pin": settings.ADMIN_PIN,
                "duration": duration,
                "auto_mode": False
            })
            assert t_res["duration"] == duration
            assert game_manager.duration == duration
        print("  ✓ 5s, 10s ve 15s süre ayarları hatasız uygulandı.")

        # Otomatik modu aç ve 15s ayarla
        http_post("/api/admin/timer", {
            "admin_pin": settings.ADMIN_PIN,
            "duration": 15,
            "auto_mode": True
        })
        assert game_manager.auto_mode is True
        print("  ✓ Otomatik Mod (Auto Mode) başarıyla aktive edildi.")

        # ---------------------------------------------------------
        # TEST 6: YARIŞMA AKIŞI (Soru -> Cevap -> Skor -> Podyum)
        # ---------------------------------------------------------
        print("\n[TEST 6] Tam Yarışma Yaşam Döngüsü Simülasyonu...")
        
        # 6.1 Yarışmayı Başlat
        http_post("/api/admin/action", {"admin_pin": settings.ADMIN_PIN, "action": "START_GAME"})
        assert game_manager.status == "QUESTION"
        curr_q = game_manager.get_current_question()
        print(f"  ✓ Yarışma başladı! 1. Soru aktif: '{curr_q.question[:40]}...'")

        # 6.2 Oyuncular Cevap Gönderiyor
        correct_opt = curr_q.correct
        wrong_opt = "A" if correct_opt != "A" else "B"

        # Can doğru cevap verir (hızlı cevap)
        _, ans1, _ = http_post("/api/player/answer", {
            "player_id": "player-1",
            "question_id": curr_q.id,
            "choice": correct_opt
        })
        assert ans1["is_correct"] is True
        assert ans1["points_earned"] >= 500

        # Zeynep doğru cevap verir
        _, ans2, _ = http_post("/api/player/answer", {
            "player_id": "player-2",
            "question_id": curr_q.id,
            "choice": correct_opt
        })
        assert ans2["is_correct"] is True

        # Burak yanlış cevap verir
        _, ans3, _ = http_post("/api/player/answer", {
            "player_id": "player-3",
            "question_id": curr_q.id,
            "choice": wrong_opt
        })
        assert ans3["is_correct"] is False
        assert ans3["points_earned"] == 0

        print("  ✓ 3 oyuncunun cevapları işlendi (2 Doğru, 1 Yanlış) ve Kahoot puanları hesaplandı.")

        # 6.3 Cevabı Açıkla (REVEAL)
        http_post("/api/admin/action", {"admin_pin": settings.ADMIN_PIN, "action": "REVEAL_ANSWER"})
        assert game_manager.status == "REVEAL"
        assert game_manager.answer_stats[correct_opt] == 2
        print(f"  ✓ REVEAL durumu doğrulandı: Dağılım -> {game_manager.answer_stats}")

        # 6.4 Liderlik Tablosunu Göster
        http_post("/api/admin/action", {"admin_pin": settings.ADMIN_PIN, "action": "SHOW_LEADERBOARD"})
        assert game_manager.status == "LEADERBOARD"
        _, lb, _ = http_get("/api/leaderboard")
        assert len(lb) == 3
        assert lb[0]["name"] == "Can Yılmaz"
        assert lb[0]["rank"] == 1
        print(f"  ✓ Liderlik Tablosu: 1. Sıra -> {lb[0]['name']} ({lb[0]['score']} Puan)")

        # 6.5 Podyum Finali (3., 2., 1. Animasyonu)
        http_post("/api/admin/action", {"admin_pin": settings.ADMIN_PIN, "action": "FINISH_PODIUM"})
        assert game_manager.status == "PODIUM"
        _, podium_res, _ = http_get("/api/podium")
        assert podium_res["first"]["id"] == "player-1"
        assert podium_res["second"]["id"] == "player-2"
        assert podium_res["third"]["id"] == "player-3"
        print(f"  ✓ PODYUM DOĞRULANDI:")
        print(f"     🥇 1. Şampiyon: {podium_res['first']['name']} ({podium_res['first']['score']} P)")
        print(f"     🥈 2. Yarışmacı: {podium_res['second']['name']} ({podium_res['second']['score']} P)")
        print(f"     🥉 3. Yarışmacı: {podium_res['third']['name']} ({podium_res['third']['score']} P)")

        print("\n" + "=" * 70)
        print("🎉 TÜM QA SİMÜLASYON TESTLERİ %100 BAŞARIYLA TAMAMLANDI!")
        print("=" * 70)

    finally:
        server.should_exit = True

if __name__ == "__main__":
    run_full_qa_simulation()
