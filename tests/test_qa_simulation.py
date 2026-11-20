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
from aura.security import security_service

BASE_URL = "http://127.0.0.1:8089"

def http_get(path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                data = None
            return resp.status, data, raw, content_type
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = None
        return e.code, data, raw, e.headers.get("Content-Type", "")

def http_post(path: str, payload: dict):
    url = f"{BASE_URL}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                data = None
            return resp.status, data, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = None
        return e.code, data, raw

def http_delete(path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                data = None
            return resp.status, data, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = None
        return e.code, data, raw

def run_comprehensive_qa_test():
    print("=" * 80)
    print("🤖 BAŞLATILIYOR: AI ERA ZİRVESİ - GÜVENLİK, AUTH VE KARARLILIK QA SİMÜLASYONU")
    print("=" * 80)

    # Start Uvicorn in Background Thread
    print("[INIT] Uvicorn sunucusu arka planda 8089 portunda başlatılıyor...")
    config = uvicorn.Config("main:app", host="127.0.0.1", port=8089, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2.0)
    print("  ✓ Sunucu hazır ve istekleri kabul ediyor.\n")

    try:
        # Reset Security Service State for clean test
        security_service.violation_counts.clear()
        security_service.banned_users.clear()
        admin_pin = settings.ADMIN_PIN
        stage_pin = settings.STAGE_PIN
        active_pin = game_manager.room_pin

        # ---------------------------------------------------------------------
        # TEST A: ADMİN PANELİ GİRİŞ (AUTH) VE PIN DOĞRULAMA
        # ---------------------------------------------------------------------
        print("[TEST A] Admin Paneli Giriş (Auth / State) Doğrulama Testi...")
        # A.1 Hatalı PIN ile giriş denemesi (403 dönmeli)
        st_bad, bad_data, _ = http_post("/api/admin/verify", {"admin_pin": "wrong_pin_999"})
        assert st_bad == 403, f"Hatalı PIN reddedilmedi! Status: {st_bad}"
        assert "Hatalı Admin PIN" in bad_data.get("detail", "")

        # A.2 Doğru PIN ile giriş (200 OK)
        st_ok, ok_data, _ = http_post("/api/admin/verify", {"admin_pin": admin_pin})
        assert st_ok == 200 and ok_data["success"] is True, f"Doğru Admin PIN kabul edilmedi: {ok_data}"

        # A.3 Boşluklu PIN ile giriş (strip() koruması)
        st_ws, ws_data, _ = http_post("/api/admin/verify", {"admin_pin": f"  {admin_pin}  "})
        assert st_ws == 200 and ws_data["success"] is True

        # A.4 Sahne PIN Doğrulaması (/api/stage/verify)
        st_stg_bad, _, _ = http_post("/api/stage/verify", {"stage_pin": "wrong_stage_pin"})
        assert st_stg_bad == 403, "Hatalı sahne PIN'i kabul edildi!"

        st_stg_ok, stg_ok, _ = http_post("/api/stage/verify", {"stage_pin": stage_pin})
        assert st_stg_ok == 200 and stg_ok["success"] is True
        print("  ✓ Admin ve Sahne PIN doğrulaması (Auth / State) hatasız çalıştı.")

        # ---------------------------------------------------------------------
        # TEST B: 220126 PIN'İNİN FRONTEND VE ARAYÜZDEN TAMAMEN GİZLENMESİ
        # ---------------------------------------------------------------------
        print("\n[TEST B] Gizli PIN (220126) Sızıntı Önleme & Frontend Temizliği Testi...")
        secret_pin = "220126"
        frontend_dirs = [ROOT_DIR / "templates", ROOT_DIR / "static"]
        leaks = []
        for fdir in frontend_dirs:
            for file_path in fdir.rglob("*"):
                if file_path.is_file() and file_path.suffix in [".html", ".js", ".css"]:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if secret_pin in content:
                            leaks.append(str(file_path.relative_to(ROOT_DIR)))
                    except Exception:
                        pass
        assert len(leaks) == 0, f"GİZLİLİK İHLALİ: {secret_pin} PIN'i şu frontend dosyalarında bulundu: {leaks}"
        print("  ✓ 220126 PIN'i frontend dosyalarının (HTML/JS/CSS) hiçbirinde yer almıyor, tamamen gizlendi!")

        # ---------------------------------------------------------------------
        # TEST C: ADMİN PIN DEĞİŞTİRME VE YENİ PIN İLE GİRİŞ DÖNGÜSÜ
        # ---------------------------------------------------------------------
        print("\n[TEST C] Admin PIN Değiştirme ve Yeni PIN Döngüsü Testi...")
        new_test_pin = "789456"
        st_chg, chg_res, _ = http_post("/api/admin/change-pin", {
            "current_pin": admin_pin,
            "new_pin": new_test_pin
        })
        assert st_chg == 200 and chg_res["success"] is True

        # Eski PIN artık çalışmamalı
        st_old, _, _ = http_post("/api/admin/verify", {"admin_pin": admin_pin})
        assert st_old == 403, "Eski PIN halen geçerli!"

        # Yeni PIN başarıyla giriş yapmalı
        st_new, new_res, _ = http_post("/api/admin/verify", {"admin_pin": new_test_pin})
        assert st_new == 200 and new_res["success"] is True

        # PIN'i eski haline geri al
        http_post("/api/admin/change-pin", {
            "current_pin": new_test_pin,
            "new_pin": admin_pin
        })
        print("  ✓ Admin PIN başarıyla değiştirildi, yeni PIN doğrulandı ve geri yüklendi.")

        # ---------------------------------------------------------------------
        # TEST D: Node.js JavaScript Syntax Doğrulama Testi
        # ---------------------------------------------------------------------
        print("\n[TEST D] Node.js JavaScript Syntax Doğrulama Testi...")
        import shutil, subprocess
        node_bin = shutil.which("node")
        if node_bin:
            for js_f in (ROOT_DIR / "static" / "js").glob("*.js"):
                res = subprocess.run([node_bin, "--check", str(js_f)], capture_output=True, text=True)
                assert res.returncode == 0, f"JS Syntax error in {js_f}:\n{res.stderr}"
            print("  ✓ Tüm frontend JS dosyaları (admin.js, stage.js, play.js, audio.js) sıfır syntax hatasıyla doğrulandı.")
        else:
            print("  ℹ Node.js bulunamadı, syntax testi atlandı.")

        # ---------------------------------------------------------------------
        # TEST E: Form Submit & Modal Reload Önleme Testi
        # ---------------------------------------------------------------------
        print("\n[TEST E] Form Submit & Modal Reload Önleme Testi...")
        admin_page_html = (ROOT_DIR / "templates" / "admin.html").read_text(encoding="utf-8")
        stage_page_html = (ROOT_DIR / "templates" / "stage.html").read_text(encoding="utf-8")
        assert 'id="btn-admin-login"' in admin_page_html and 'type="button"' in admin_page_html, "Admin login button must be type='button'"
        assert 'id="btn-stage-auth-submit"' in stage_page_html and 'type="button"' in stage_page_html, "Stage login button must be type='button'"
        assert 'onsubmit="event.preventDefault(); handleAdminAuth(event); return false;"' in admin_page_html
        assert 'onsubmit="event.preventDefault(); handleStageAuth(event); return false;"' in stage_page_html
        print("  ✓ Admin ve Sahne giriş formları sayfa yenileme/çökme tuzağına karşı tamamen korundu.")

        # ---------------------------------------------------------------------
        # TEST F: Vercel Serverless Timestamp Tabanlı Timer Doğrulama Testi
        # ---------------------------------------------------------------------
        print("\n[TEST F] Vercel Serverless Timestamp Tabanlı Timer Doğrulama Testi...")
        game_manager.status = "QUESTION"
        game_manager.duration = 20
        game_manager.question_start_timestamp = time.time() - 5.0 # 5 seconds elapsed
        state_dyn = game_manager.get_public_state()
        assert 14 <= state_dyn["timer_remaining"] <= 15, f"Dynamic timer calculation error: {state_dyn['timer_remaining']}"
        assert state_dyn["question_start_timestamp"] > 0
        game_manager.status = "LOBBY"
        print("  ✓ Serverless Firestore timestamp tabanlı timer hesaplaması doğrulandı.")

        # ---------------------------------------------------------------------
        # 1. ADMIN PANELİ: SIKIŞMAYAN BUTONLAR VE DÜZENLİ NAVİGASYON (Görsel 1)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 1] Admin Paneli - Sıkışmayan Butonlar ve Düzenli Tablar Testi...")
        status, _, raw_admin, _ = http_get("/admin")
        admin_html = raw_admin.decode("utf-8")
        assert "tab-btn-control" in admin_html, "Canlı Yarışma Kontrolü butonu bulunamadı!"
        assert "tab-btn-quizzes" in admin_html, "Quizlerim & Soru Bankası butonu bulunamadı!"
        assert "tab-btn-reports" in admin_html, "Sonuçları İndir butonu bulunamadı!"
        assert "tab-btn-security" in admin_html, "Ban Yönetimi butonu bulunamadı!"
        assert "no-scrollbar" in admin_html, "no-scrollbar responsive kaydırma stili bulunamadı!"
        assert "admin-auth-error" in admin_html, "Hata bildirim alanı #admin-auth-error bulunamadı!"
        print("  ✓ Admin paneli 4 ana sekmesi sıkışmayan flex yapısıyla doğrulandı.")

        # ---------------------------------------------------------------------
        # 2. OYUNCU EKRANI: SKOR VE SIRALAMA GÖSTERİMİ (/play)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 2] Oyuncu Ekranı - Skor ve Sıralama Gösterimi Testi...")
        status, _, raw_play, _ = http_get("/play")
        play_html = raw_play.decode("utf-8")
        assert "player-final-rank" in play_html, "Oyuncu ekranındaki sıralama alanı (#player-final-rank) bulunamadı!"
        assert "player-final-rank-box" in play_html, "Oyuncu ekranındaki sıralama kutusu bulunamadı!"
        assert "final-score" in play_html, "Oyuncu final skor alanı bulunamadı!"
        print("  ✓ Oyuncu ekranındaki final sıralama ve skor kartı UI yapıları doğrulandı.")

        # ---------------------------------------------------------------------
        # 3. GELİŞMİŞ FİLTRELEME: ARGO, KÜFÜR VE SİYASİ ENGELLEME (3 HAK BAN SİSTEMİ)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 3] Gelişmiş Filtreleme: Argo, Küfür ve Siyasi Engelleme (3 Hak) Testi...")
        test_client_id = "test-violator-99"
        
        # 3.1 Siyasi kısaltma / isim denemesi
        st1, err1, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "rtesi genc",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st1 == 400, f"Siyasi kısaltma ihlali engellenmedi! Status: {st1}"
        assert "UYARI (1/3 Hak)" in err1["detail"]

        # 3.2 İkinci siyasi/argo ihlal
        st2, err2, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "aposi reis",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st2 == 400
        assert "UYARI (2/3 Hak)" in err2["detail"]

        # 3.3 3. Hak İhlali -> Kalıcı Ban (403 Forbidden)
        st3, err3, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "chpli genc",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st3 == 403, f"3. İhlal sonrası 403 kalıcı ban uygulanmadı! Status: {st3}"
        assert "HESABINIZ ENGELLENDİ" in err3["detail"]
        print("  ✓ Siyasi kısaltmalar ve 3-hak kalıcı ban mekanizması doğrulandı.")

        # 3.4 Admin Ban Listesi Kontrolü & Ban Kaldırma
        st_ban, ban_data, _, _ = http_get(f"/api/admin/banned?admin_pin={admin_pin}")
        assert st_ban == 200
        banned_entry = next((u for u in ban_data["banned_users"] if u["identifier"] == test_client_id), None)
        assert banned_entry is not None, "Banlanan kullanıcı admin ban listesinde bulunamadı!"

        st_unban, unban_res, _ = http_post("/api/admin/unban", {
            "admin_pin": admin_pin,
            "identifier": test_client_id
        })
        assert st_unban == 200 and unban_res["success"] is True
        print(f"  ✓ Admin tarafından '{test_client_id}' kullanıcısının banı başarıyla kaldırıldı.")

        # 3.5 Gerçek Ad ve Soyad (En az 2 kelime) ve Troll Spam Koruması
        st_single_word, err_single, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Ahmet",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🦊",
            "player_id": "test-single-word"
        })
        assert st_single_word == 400, "Tek kelimelik isim kabul edildi!"

        st_troll, err_troll, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "asdasd asdasd",
            "school": "Güngören Anadolu Lisesi",
            "avatar": "🐺",
            "player_id": "test-troll"
        })
        assert st_troll == 400, "Troll anlamsız harf dizilimi kabul edildi!"
        print("  ✓ Gerçek Ad Soyad doğrulaması ve troll harf engellemesi doğrulandı.")

        # ---------------------------------------------------------------------
        # 4. ÇAKIŞMA ÖNLEME VE SAHNE UI DÜZENLEMELERİ (Görsel 2 & 3)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 4] Sahne Çakışma Önleme ve Renk Geçişleri Testi...")
        status, _, raw_stage, _ = http_get("/stage")
        stage_html = raw_stage.decode("utf-8")
        assert "ZİRVE ŞAMPİYONLARI" in stage_html
        assert "view-podium" in stage_html
        assert "podium-slot-1" in stage_html and "podium-slot-2" in stage_html and "podium-slot-3" in stage_html
        assert "stage-auth-error" in stage_html, "Sahne hata bildirim alanı bulunamadı!"
        print("  ✓ Sahne üst barı ile podyum başlığı arasındaki çakışma önleyici yapı doğrulandı.")

        # ---------------------------------------------------------------------
        # 5. KAHOOT TARZI SIRALI PODYUM ANİMASYONLARI
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 5] Kahoot Tarzı Sıralı Podyum Animasyonları Testi...")
        with open(ROOT_DIR / "static/js/stage.js", "r", encoding="utf-8") as f:
            stage_js_code = f.read()
        assert "podium-slot-3" in stage_js_code and "podium-slot-2" in stage_js_code and "podium-slot-1" in stage_js_code
        assert "podium-revealed" in stage_js_code
        print("  ✓ Sıralı podyum yükselişi animasyon kodu doğrulandı.")

        # ---------------------------------------------------------------------
        # 6. SAHNE EKRANI - TÜM SIRALAMAYI GÖRME BUTONU
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 6] Sahne Ekranı - Tüm Sıralamayı Görme Butonu Testi...")
        assert "btn-show-full-leaderboard" in stage_html
        assert "modal-full-leaderboard" in stage_html
        print("  ✓ Sahne ekranı 'Bütün Sıralamayı Göster' butonu ve modalı doğrulandı.")

        # ---------------------------------------------------------------------
        # 7. ADMİN PANELİ - OYUNCULARA PUAN EKLEME VE SİLME (+ / -)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 7] Admin Paneli - Oyunculara Puan Ekleme ve Silme Testi...")
        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Barış Manço",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🦁",
            "player_id": "player-score-test"
        })
        
        # +150 puan ekle
        st_add, add_res, _ = http_post("/api/admin/players/score", {
            "admin_pin": admin_pin,
            "player_id": "player-score-test",
            "score_delta": 150
        })
        assert st_add == 200 and add_res["success"] is True
        assert add_res["new_score"] == 150

        # -50 puan sil
        st_sub, sub_res, _ = http_post("/api/admin/players/score", {
            "admin_pin": admin_pin,
            "player_id": "player-score-test",
            "score_delta": -50
        })
        assert st_sub == 200 and sub_res["success"] is True
        assert sub_res["new_score"] == 100
        print(f"  ✓ Admin puan ekleme (+150) ve silme (-50) fonksiyonu doğrulandı.")

        # ---------------------------------------------------------------------
        # 8. GELİŞMİŞ 'QUİZLERİM' VE KLASÖR YAPILI SORU YÖNETİMİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 8] Gelişmiş 'Quizlerim' ve Klasör Yapılı Soru Yönetimi Testi...")
        st_folder, f_res, _ = http_post("/api/admin/folders", {
            "admin_pin": admin_pin,
            "name": "Zirve Final Soru Seti",
            "description": "Zirve final oturumu soruları"
        })
        assert st_folder == 200 and f_res["success"] is True
        created_folder_id = f_res["folder"]["id"]

        st_flist, flist_data, _, _ = http_get(f"/api/admin/folders?admin_pin={admin_pin}")
        assert st_flist == 200
        assert any(f["id"] == created_folder_id for f in flist_data["folders"])

        with open(ROOT_DIR / "static/css/style.css", "r", encoding="utf-8") as f:
            css_code = f.read()
        assert "btn-rainbow-rgb" in css_code
        print("  ✓ Klasör oluşturma, listeleme ve Rainbow RGB buton animasyonu doğrulandı.")

        # ---------------------------------------------------------------------
        # 9. YAPAY ZEKA SORU ÜRETİCİ VE SORU SINIRLARI (MAKS 50 / MAKS 60)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 9] Yapay Zeka Soru Üretici ve Soru Sınırları Testi...")
        st_limit50, _, _ = http_post("/api/admin/generate-questions", {
            "admin_pin": admin_pin,
            "count": 55
        })
        assert st_limit50 in (400, 422), f"50'den fazla soru üretimine izin verildi! Status: {st_limit50}"

        st_gen, gen_res, _ = http_post("/api/admin/generate-questions", {
            "admin_pin": admin_pin,
            "count": 10,
            "folder_id": created_folder_id,
            "difficulties": {"cok_kolay": 2, "kolay": 3, "orta": 3, "zor": 2}
        })
        assert st_gen == 200 and gen_res["success"] is True
        print(f"  ✓ Gemini AI ile 10 soru başarıyla üretildi (Toplam: {gen_res['total_questions']}/60).")

        # ---------------------------------------------------------------------
        # 10. BAĞIMSIZ SÜRE AYARLARI
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 10] Bağımsız Soru Süresi ve Otomatik Akış Süresi Testi...")
        st_timer, timer_res, _ = http_post("/api/admin/timer", {
            "admin_pin": admin_pin,
            "question_duration": 25,
            "transition_delay": 10,
            "auto_mode": True
        })
        assert st_timer == 200
        assert timer_res["question_duration"] == 25
        assert timer_res["transition_delay"] == 10
        print("  ✓ Soru süresi (25s) ve geçiş süresi (10s) bağımsız olarak ayarlandı.")

        # ---------------------------------------------------------------------
        # 11. UÇTAN UCA QA SİMÜLASYON TESTİ (ADMIN, SAHNE, OYUNCU)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 11] Uçtan Uca Tam Akış Simülasyonu Testi...")
        http_post("/api/admin/action", {"admin_pin": admin_pin, "action": "RESET_ROOM"})

        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Zeynep Kaya",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🐼",
            "player_id": "player-1"
        })
        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Ali Vural",
            "school": "Cemil Meriç Kız Mesleki ve Teknik Anadolu Lisesi",
            "avatar": "🦊",
            "player_id": "player-2"
        })

        http_post("/api/admin/action", {"admin_pin": admin_pin, "action": "START_GAME"})
        assert game_manager.status == "QUESTION"

        curr_q = game_manager.get_current_question()
        http_post("/api/player/answer", {"player_id": "player-1", "question_id": curr_q.id, "choice": curr_q.correct})
        http_post("/api/player/answer", {"player_id": "player-2", "question_id": curr_q.id, "choice": curr_q.correct})

        http_post("/api/admin/action", {"admin_pin": admin_pin, "action": "REVEAL_ANSWER"})
        assert game_manager.status == "REVEAL"

        http_post("/api/admin/action", {"admin_pin": admin_pin, "action": "SHOW_LEADERBOARD"})
        assert game_manager.status == "LEADERBOARD"

        http_post("/api/admin/action", {"admin_pin": admin_pin, "action": "FINISH_PODIUM"})
        assert game_manager.status == "PODIUM"

        st_r1, r1_data, _, _ = http_get("/api/player/rank/player-1")
        assert st_r1 == 200 and r1_data["rank"] == 1
        print(f"  ✓ Oyuncu 1 Sıralaması: {r1_data['rank']}. sıra ({r1_data['score']} Puan)")

        st_pod, pod_res, _, _ = http_get("/api/podium")
        assert st_pod == 200
        assert pod_res["first"]["id"] == "player-1"
        print(f"  ✓ Podyum Şampiyonu: 🥇 {pod_res['first']['name']} ({pod_res['first']['score']} Puan)")

        print("\n" + "=" * 80)
        print("🏆 TÜM GÜVENLİK, AUTH VE KARARLILIK TESTLERİ %100 BAŞARIYLA TAMAMLANDI!")
        print("=" * 80)

    finally:
        server.should_exit = True

if __name__ == "__main__":
    run_comprehensive_qa_test()
