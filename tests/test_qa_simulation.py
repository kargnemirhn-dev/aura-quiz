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
    print("🤖 BAŞLATILIYOR: AI ERA ZİRVESİ - GÜNCELLENMİŞ EKSİKSİZ QA TEST SİMÜLASYONU")
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
        # TEST 1: SAYFA VE GÖRSEL METİN DÜZELTMELERİ
        # ---------------------------------------------------------
        print("[TEST 1] Görsel ve Metin Düzeltmeleri Testi...")
        
        # 1.1 Portal (/)
        status, _, text = http_get("/")
        assert status == 200, "Portal açılmadı"
        # Başlık kontrolü
        assert "AI ERA: TEKNOLOJİ & GİRİŞİMCİLİK ZİRVESİ" in text, "Ana başlık metni hatalı!"
        # Hoş geldiniz metni kontrolü (Gereksinim 1)
        assert "Yapay zekanın ve girişimcilik ekosisteminin nabzını tutan, gerçek zamanlı bilgi yarışması portalına hoş geldiniz." in text, "Hoş geldiniz metni hatalı!"
        # Rozet & Yeşil yanıp sönen nokta kontrolü
        assert "Canlı Eşzamanlı Bilgi Yarışma Portalı" in text, "Rozet metni güncellenmemiş!"
        assert "live-green-dot" in text, "Yeşil parlayan canlılık noktası (pulsing green dot) bulunamadı!"
        # Kartların taşma sorununa karşı viewport kontrolü
        assert "min-h-screen" in text and "max-w-5xl" in text, "Kart taşmasını önleyen CSS optimize container bulunamadı!"
        print("  ✓ Portal (/): Başlık, profesyonel karşılama metni, yeşil parlayan nokta ve kart düzeni doğrulandı.")

        # 1.2 Sahne Ekranı Güvenliği & Arayüz (/stage)
        status, _, text_stage = http_get("/stage")
        assert status == 200, "Stage sayfası açılmadı"
        # a) Sahne Ekranı Güvenlik Kilidi Modalı (Gereksinim 3)
        assert "modal-stage-auth" in text_stage, "Sahne ekranı güvenlik şifre modalı bulunamadı!"
        # Sahne PIN Yetkilendirmesi Testi
        stage_bad, _, _ = http_post("/api/stage/verify", {"stage_pin": "000000"})
        assert stage_bad == 403, "Yetkisiz Sahne PIN engellenmedi!"
        stage_ok, _, _ = http_post("/api/stage/verify", {"stage_pin": "220126"})
        assert stage_ok == 200, "Varsayılan Sahne PIN (220126) yetkilendirilemedi!"
        # b) QR Kod Büyütme Modalı
        assert "modal-qr" in text_stage, "QR Büyütme modalı bulunamadı!"
        # c) C şıkkı sarı rengi (bg-yellow-500)
        assert "bg-yellow-500" in text_stage, "C şıkkı sarı rengi (bg-yellow-500) bulunamadı!"
        # d) Yatay kayan katılımcı kartları
        assert "marquee-content" in text_stage, "Yatay kayan katılımcı marquee alanı bulunamadı!"
        # e) Podyum animasyonu (3., 2., 1.)
        assert "podium-1" in text_stage and "podium-2" in text_stage and "podium-3" in text_stage, "Podyum basamakları bulunamadı!"
        # f) Otomatik mod geri sayım göstergesi
        assert "leaderboard-auto-countdown" in text_stage, "Liderlik tablosu 5s geri sayım alanı bulunamadı!"
        print("  ✓ Sahne Ekranı (/stage): Güvenlik kilidi (220126), QR Modal, C-yellow (bg-yellow-500), Marquee, 5s Countdown ve Podyum doğrulandı.")

        # 1.3 Oyuncu Ekranı ve Google Tarzı Hayvan Avatarları (/play)
        status, _, text_play = http_get("/play")
        assert status == 200, "Play sayfası açılmadı"
        # a) "Avatar Seç" butonu ve Google tarzı hayvan modalı (Gereksinim 2)
        assert "Avatar Seç" in text_play, "Avatar Seç butonu bulunamadı!"
        assert "modal-avatar" in text_play, "Google tarzı hayvan avatarı modalı bulunamadı!"
        # b) "Odadan Çık" butonu
        assert "Odadan Çık" in text_play, "Odadan Çık butonu bulunamadı!"
        # c) Kahoot renkleri/simgeleri (🔺, 🔷, 🟡, 🟢)
        assert "🔺" in text_play and "🔷" in text_play and "🟡" in text_play and "🟢" in text_play
        # d) Telefonda soru metni veya şık yazılarının olmaması kuralı:
        assert "stage-text-A" not in text_play, "Oyuncu ekranında soru metni veya şık yazısı yer almamalı!"
        print("  ✓ Oyuncu Ekranı (/play): Google tarzı hayvan avatarı modalı, 'Odadan Çık' ve Kahoot butonları doğrulandı.")

        # ---------------------------------------------------------
        # TEST 2: GÜVENLİK, 6 HANELİ ODA PIN VE ADMIN PIN SİSTEMİ
        # ---------------------------------------------------------
        print("\n[TEST 2] Güvenlik, 6 Haneli Oda PIN ve Admin PIN Değiştirme Testi...")
        
        # 2.1 Varsayılan Admin PIN (220126) Doğrulaması
        admin_bad, _, _ = http_post("/api/admin/verify", {"admin_pin": "123456"})
        assert admin_bad == 403, "Hatalı Admin PIN reddedilmedi!"
        admin_good, good_data, _ = http_post("/api/admin/verify", {"admin_pin": "220126"})
        assert admin_good == 200 and good_data["success"] is True, "Varsayılan Admin PIN (220126) ile giriş yapılamadı!"
        print("  ✓ Varsayılan Admin PIN: '220126' başarıyla doğrulandı.")

        # 2.2 6 Haneli Rastgele Oda PIN Üretimi
        rnd_status, rnd_data, _ = http_post("/api/admin/random-pin", {"admin_pin": "220126"})
        assert rnd_status == 200, "Rastgele PIN üretilemedi"
        random_pin = rnd_data["room_pin"]
        assert len(random_pin) == 6 and random_pin.isdigit(), f"PIN 6 haneli sayı olmalıdır, üretilen: {random_pin}"
        print(f"  ✓ 6 Haneli Rastgele Oda PIN üretildi: '{random_pin}'")

        # 2.3 Manuel Oda PIN Güncelleme
        manual_pin = "741852"
        up_status, up_data, _ = http_post("/api/admin/pin", {"admin_pin": "220126", "new_room_pin": manual_pin})
        assert up_status == 200 and up_data["room_pin"] == manual_pin
        _, state_now, _ = http_get("/api/state")
        assert state_now["room_pin"] == manual_pin
        print(f"  ✓ Manuel 6 Haneli Oda PIN güncellendi: '{manual_pin}'")

        # 2.4 Admin PIN Değiştirme Fonksiyonu (Gereksinim 3)
        ch_status, ch_data, _ = http_post("/api/admin/change-pin", {
            "current_pin": "220126",
            "new_pin": "987654"
        })
        assert ch_status == 200 and ch_data["success"] is True, "Admin PIN değiştirilemedi!"
        # Yeni PIN ile doğrula
        v_new, _, _ = http_post("/api/admin/verify", {"admin_pin": "987654"})
        assert v_new == 200
        # Eski PIN artık çalışmamalı
        v_old, _, _ = http_post("/api/admin/verify", {"admin_pin": "220126"})
        assert v_old == 403
        print("  ✓ 'Admin PIN Değiştir' fonksiyonu başarıyla test edildi (220126 -> 987654).")

        # Geriye 220126 olarak alalım
        http_post("/api/admin/change-pin", {"current_pin": "987654", "new_pin": "220126"})
        assert settings.ADMIN_PIN == "220126"

        # ---------------------------------------------------------
        # TEST 3: GEMINI AI VE 30 ÖZGÜN SORU
        # ---------------------------------------------------------
        print("\n[TEST 3] Gemini Soru Bankası Testi (30 Soru)...")
        assert len(game_manager.questions) == 30, f"30 soru bekleniyordu, {len(game_manager.questions)} bulundu."
        for idx, q in enumerate(game_manager.questions, 1):
            assert q.id == idx
            assert q.correct in ("A", "B", "C", "D")
            assert q.options.A and q.options.B and q.options.C and q.options.D
        print("  ✓ 30 adet yapay zeka & girişimcilik sorusu eksiksiz doğrulandı.")

        # ---------------------------------------------------------
        # TEST 4: OYUNCU KATILIMI, HAYVAN AVATARLARI VE ODADAN ÇIKIŞ
        # ---------------------------------------------------------
        print("\n[TEST 4] Çoklu Oyuncu Katılımı (Hayvan Avatarları) ve Kahoot Akışı...")
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "RESET_ROOM"})

        # Panda, Tilki ve Kurt avatarlarıyla katılım
        status, p1, _ = http_post("/api/player/join", {
            "room_pin": manual_pin,
            "name": "Can Yılmaz",
            "school": "İTÜ Yapay Zeka Kulübü",
            "avatar": "🐼",
            "player_id": "player-1"
        })
        assert p1["success"] is True and p1["player"]["avatar"] == "🐼"

        status, p2, _ = http_post("/api/player/join", {
            "room_pin": manual_pin,
            "name": "Zeynep Kaya",
            "school": "Boğaziçi Girişimcilik",
            "avatar": "🦊",
            "player_id": "player-2"
        })
        assert p2["success"] is True and p2["player"]["avatar"] == "🦊"

        status, p3, _ = http_post("/api/player/join", {
            "room_pin": manual_pin,
            "name": "Burak Demir",
            "school": "ODTÜ Bilgisayar",
            "avatar": "🐺",
            "player_id": "player-3"
        })
        assert p3["success"] is True and p3["player"]["avatar"] == "🐺"

        assert len(game_manager.players) == 3
        print("  ✓ 3 oyuncu sevimli hayvan avatarlarıyla (🐼 Panda, 🦊 Tilki, 🐺 Kurt) katıldı.")

        # Odadan Çık Testi
        _, leave_data, _ = http_post("/api/player/leave", {"player_id": "player-3"})
        assert leave_data["success"] is True
        assert len(game_manager.players) == 2
        print("  ✓ 'Odadan Çık' fonksiyonu test edildi: Oyuncu odadan ayrıldı.")

        # Oyuncu tekrar katılsın
        http_post("/api/player/join", {
            "room_pin": manual_pin,
            "name": "Burak Demir",
            "school": "ODTÜ Bilgisayar",
            "avatar": "🐺",
            "player_id": "player-3"
        })

        # ---------------------------------------------------------
        # TEST 5: SAYAÇLAR (5s/10s/15s) VE OTOMATİK MOD GERİ SAYIM
        # ---------------------------------------------------------
        print("\n[TEST 5] Sayaç Süreleri ve Otomatik Mod...")
        for dur in (5, 10, 15):
            _, t_res, _ = http_post("/api/admin/timer", {"admin_pin": "220126", "duration": dur, "auto_mode": False})
            assert t_res["duration"] == dur
        print("  ✓ 5s, 10s ve 15s süre ayarları hatasız doğrulandı.")

        # Otomatik modu aç
        http_post("/api/admin/timer", {"admin_pin": "220126", "duration": 15, "auto_mode": True})
        assert game_manager.auto_mode is True
        print("  ✓ Otomatik Mod (Auto Mode) başarıyla aktive edildi.")

        # ---------------------------------------------------------
        # TEST 6: TAM YARIŞMA DÖNGÜSÜ VE PODYUM
        # ---------------------------------------------------------
        print("\n[TEST 6] Tam Yarışma Yaşam Döngüsü Simülasyonu...")
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "START_GAME"})
        assert game_manager.status == "QUESTION"
        curr_q = game_manager.get_current_question()
        correct_opt = curr_q.correct

        # Oyuncular Kahoot butonlarıyla cevap veriyor
        http_post("/api/player/answer", {"player_id": "player-1", "question_id": curr_q.id, "choice": correct_opt})
        http_post("/api/player/answer", {"player_id": "player-2", "question_id": curr_q.id, "choice": correct_opt})
        http_post("/api/player/answer", {"player_id": "player-3", "question_id": curr_q.id, "choice": "A" if correct_opt != "A" else "B"})

        # Reveal
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "REVEAL_ANSWER"})
        assert game_manager.status == "REVEAL"

        # Leaderboard (5s countdown kontrolü)
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "SHOW_LEADERBOARD"})
        assert game_manager.status == "LEADERBOARD"
        _, lb_state, _ = http_get("/api/state")
        assert "leaderboard_countdown" in lb_state
        print("  ✓ Liderlik tablosu 5 saniyelik otomatik geçiş sayacı devrede.")

        # Finale & Podyum
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "FINISH_PODIUM"})
        assert game_manager.status == "PODIUM"
        _, podium, _ = http_get("/api/podium")
        assert podium["first"]["id"] == "player-1"
        print(f"  ✓ PODYUM 3-2-1:")
        print(f"     🥇 1. Şampiyon: {podium['first']['avatar']} {podium['first']['name']} ({podium['first']['score']} P)")
        print(f"     🥈 2. Yarışmacı: {podium['second']['avatar']} {podium['second']['name']} ({podium['second']['score']} P)")
        print(f"     🥉 3. Yarışmacı: {podium['third']['avatar']} {podium['third']['name']} ({podium['third']['score']} P)")

        print("\n" + "=" * 70)
        print("🎉 TÜM YENİ GEREKSİNİMLER VE QA TESTLERİ %100 BAŞARIYLA TAMAMLANDI!")
        print("=" * 70)

    finally:
        server.should_exit = True

if __name__ == "__main__":
    run_full_qa_simulation()
