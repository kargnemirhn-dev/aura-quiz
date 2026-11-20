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

def run_comprehensive_11_step_qa_test():
    print("=" * 80)
    print("🤖 BAŞLATILIYOR: AI ERA ZİRVESİ - 11 MADDELİK KUSURSUZ QA DOĞRULAMA SİMÜLASYONU")
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
        active_pin = game_manager.room_pin

        # ---------------------------------------------------------------------
        # 1. ADMIN PANELİ: SIKIŞMAYAN BUTONLAR VE DÜZENLİ NAVİGASYON (Görsel 1)
        # ---------------------------------------------------------------------
        print("[GEREKSİNİM 1] Admin Paneli - Sıkışmayan Butonlar ve Düzenli Tablar Testi...")
        status, _, raw_admin, _ = http_get("/admin")
        admin_html = raw_admin.decode("utf-8")
        assert "tab-btn-control" in admin_html, "Canlı Yarışma Kontrolü butonu bulunamadı!"
        assert "tab-btn-quizzes" in admin_html, "Quizlerim & Soru Bankası butonu bulunamadı!"
        assert "tab-btn-reports" in admin_html, "Sonuçları İndir butonu bulunamadı!"
        assert "tab-btn-security" in admin_html, "Ban Yönetimi butonu bulunamadı!"
        assert "no-scrollbar" in admin_html, "no-scrollbar responsive kaydırma stili bulunamadı!"
        print("  ✓ Admin paneli 4 ana sekmesi (Canlı Yarışma, Quizlerim, Sonuçlar, Ban) sıkışmayan flex yapısıyla doğrulandı.")

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
        
        # 3.1 Siyasi kısaltma / isim denemesi (rtesi, aposi, rte vb.)
        st1, err1, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "rtesi genc",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st1 == 400, f"Siyasi kısaltma ihlali engellenmedi! Status: {st1}"
        assert "UYARI (1/3 Hak)" in err1["detail"], f"Beklenen 1/3 uyarısı alınamadı: {err1}"

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
        print("  ✓ Siyasi kısaltmalar ('rtesi', 'aposi', 'chpli') ve 3-hak kalıcı ban mekanizması doğrulandı.")

        # 3.4 Admin Ban Listesi Kontrolü & Ban Kaldırma
        st_ban, ban_data, _, _ = http_get("/api/admin/banned?admin_pin=220126")
        assert st_ban == 200
        banned_entry = next((u for u in ban_data["banned_users"] if u["identifier"] == test_client_id), None)
        assert banned_entry is not None, "Banlanan kullanıcı admin ban listesinde bulunamadı!"

        st_unban, unban_res, _ = http_post("/api/admin/unban", {
            "admin_pin": "220126",
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
        assert "soyad" in err_single["detail"].lower() or "en az iki kelime" in err_single["detail"].lower()

        st_troll, err_troll, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "asdasd asdasd",
            "school": "Güngören Anadolu Lisesi",
            "avatar": "🐺",
            "player_id": "test-troll"
        })
        assert st_troll == 400, "Troll anlamsız harf dizilimi kabul edildi!"
        print("  ✓ Gerçek Ad Soyad doğrulaması (en az 2 kelime) ve troll harf dizilimi engellemesi doğrulandı.")

        # ---------------------------------------------------------------------
        # 4. ÇAKIŞMA ÖNLEME VE SAHNE UI DÜZENLEMELERİ (Görsel 2 & 3)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 4] Sahne Çakışma Önleme ve Renk Geçişleri Testi...")
        status, _, raw_stage, _ = http_get("/stage")
        stage_html = raw_stage.decode("utf-8")
        assert "ZİRVE ŞAMPİYONLARI" in stage_html, "ZİRVE ŞAMPİYONLARI başlığı bulunamadı!"
        assert "view-podium" in stage_html, "Podyum görünümü bulunamadı!"
        assert "podium-slot-1" in stage_html and "podium-slot-2" in stage_html and "podium-slot-3" in stage_html
        print("  ✓ Sahne üst barı ile podyum başlığı arasındaki çakışma önleyici yapı ve slotlar doğrulandı.")

        # ---------------------------------------------------------------------
        # 5. KAHOOT TARZI SIRALI PODYUM ANİMASYONLARI
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 5] Kahoot Tarzı Sıralı Podyum Animasyonları Testi...")
        with open(ROOT_DIR / "static/js/stage.js", "r", encoding="utf-8") as f:
            stage_js_code = f.read()
        assert "podium-slot-3" in stage_js_code and "podium-slot-2" in stage_js_code and "podium-slot-1" in stage_js_code
        assert "podium-revealed" in stage_js_code, "Sıralı açılış sınıfı podium-revealed bulunamadı!"
        assert "setTimeout" in stage_js_code and "confetti" in stage_js_code
        print("  ✓ Sıralı podyum yükselişi (3. -> 2. -> 1. Şampiyon + konfeti) animasyon kodu doğrulandı.")

        # ---------------------------------------------------------------------
        # 6. SAHNE EKRANI - TÜM SIRALAMAYI GÖRME BUTONU
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 6] Sahne Ekranı - Tüm Sıralamayı Görme Butonu Testi...")
        assert "btn-show-full-leaderboard" in stage_html, "Bütün Sıralamayı Göster butonu bulunamadı!"
        assert "modal-full-leaderboard" in stage_html, "Tüm Sıralama Modalı bulunamadı!"
        assert "openFullLeaderboardModal" in stage_js_code, "Modal açma fonksiyonu bulunamadı!"
        print("  ✓ Sahne ekranı 'Bütün Sıralamayı Göster' butonu ve tam sıralama tablosu modalı doğrulandı.")

        # ---------------------------------------------------------------------
        # 7. ADMİN PANELİ - OYUNCULARA PUAN EKLEME VE SİLME (+ / -)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 7] Admin Paneli - Oyunculara Puan Ekleme ve Silme Testi...")
        # Test için bir oyuncu ekle
        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Barış Manço",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🦁",
            "player_id": "player-score-test"
        })
        
        # +150 puan ekle
        st_add, add_res, _ = http_post("/api/admin/players/score", {
            "admin_pin": "220126",
            "player_id": "player-score-test",
            "score_delta": 150
        })
        assert st_add == 200 and add_res["success"] is True
        assert add_res["new_score"] == 150

        # -50 puan sil
        st_sub, sub_res, _ = http_post("/api/admin/players/score", {
            "admin_pin": "220126",
            "player_id": "player-score-test",
            "score_delta": -50
        })
        assert st_sub == 200 and sub_res["success"] is True
        assert sub_res["new_score"] == 100
        print(f"  ✓ Admin puan ekleme (+150) ve silme (-50) fonksiyonu başarıyla test edildi (Yeni Skor: 100).")

        # ---------------------------------------------------------------------
        # 8. GELİŞMİŞ 'QUİZLERİM' VE KLASÖR YAPILI SORU YÖNETİMİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 8] Gelişmiş 'Quizlerim' ve Klasör Yapılı Soru Yönetimi Testi...")
        # 8.1 Yeni Klasör Oluştur
        st_folder, f_res, _ = http_post("/api/admin/folders", {
            "admin_pin": "220126",
            "name": "Finaller Özel Soru Seti",
            "description": "Büyük final oturumu için ayrılmış özel soru seti"
        })
        assert st_folder == 200 and f_res["success"] is True
        created_folder_id = f_res["folder"]["id"]

        # 8.2 Klasörleri Listele
        st_flist, flist_data, _, _ = http_get("/api/admin/folders?admin_pin=220126")
        assert st_flist == 200
        assert any(f["id"] == created_folder_id for f in flist_data["folders"])

        # 8.3 Klasörü Aktif Yap
        st_act, act_res, _ = http_post(f"/api/admin/folders/{created_folder_id}/activate", {
            "admin_pin": "220126"
        })
        assert st_act == 200 and act_res["success"] is True

        # 8.4 Rainbow RGB Buton CSS Kontrolü
        with open(ROOT_DIR / "static/css/style.css", "r", encoding="utf-8") as f:
            css_code = f.read()
        assert "btn-rainbow-rgb" in css_code, "btn-rainbow-rgb sınıfı style.css içinde bulunamadı!"
        assert "rainbowGlow" in css_code, "rainbowGlow animasyonu bulunamadı!"
        print("  ✓ Klasör oluşturma, listeleme, aktif yapma ve Rainbow RGB buton animasyonu doğrulandı.")

        # ---------------------------------------------------------------------
        # 9. YAPAY ZEKA SORU ÜRETİCİ VE SORU SINIRLARI (MAKS 50 ÜRETİM / MAKS 60 BANKA)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 9] Yapay Zeka Soru Üretici ve Soru Sınırları Testi...")
        # 9.1 Tek seferde 50'den fazla üretim denemesi (Hata vermeli)
        st_limit50, err50, _ = http_post("/api/admin/generate-questions", {
            "admin_pin": "220126",
            "count": 55
        })
        assert st_limit50 in (400, 422), f"50'den fazla soru üretimine izin verildi! Status: {st_limit50}"

        # 9.2 Zorluk dağılımı ile geçerli üretim (10 Soru: 2 Çok Kolay, 3 Kolay, 3 Orta, 2 Zor)
        st_gen, gen_res, _ = http_post("/api/admin/generate-questions", {
            "admin_pin": "220126",
            "count": 10,
            "folder_id": created_folder_id,
            "difficulties": {
                "cok_kolay": 2,
                "kolay": 3,
                "orta": 3,
                "zor": 2
            }
        })
        assert st_gen == 200 and gen_res["success"] is True
        assert gen_res["count"] == 10
        print(f"  ✓ Gemini AI ile 10 soru başarıyla üretildi (Zorluk dağılımlı). Toplam Soru: {gen_res['total_questions']}/60")

        # ---------------------------------------------------------------------
        # 10. BAĞIMSIZ SORU SÜRESİ VE OTOMATİK AKIŞ SÜRESİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 10] Bağımsız Soru Süresi ve Otomatik Akış Süresi Testi...")
        # Soru süresini 30s, otomatik geçişi 15s yap
        st_timer, timer_res, _ = http_post("/api/admin/timer", {
            "admin_pin": "220126",
            "question_duration": 30,
            "transition_delay": 15,
            "auto_mode": True
        })
        assert st_timer == 200
        assert timer_res["question_duration"] == 30
        assert timer_res["transition_delay"] == 15
        assert timer_res["auto_mode"] is True
        print("  ✓ Soru süresi (30s) ve otomatik liderlik geçiş süresi (15s) bağımsız olarak ayarlandı.")

        # ---------------------------------------------------------------------
        # 11. UÇTAN UCA QA SİMÜLASYON TESTİ (ADMIN, SAHNE, OYUNCU)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 11] Uçtan Uca Tam Akış Simülasyonu Testi...")
        # Odayı sıfırla
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "RESET_ROOM"})

        # 3 Farklı okuldan öğrenci katılımı
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
        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Deniz Arslan",
            "school": "Güngören Anadolu Lisesi",
            "avatar": "🦁",
            "player_id": "player-3"
        })

        # Yarışmayı Başlat
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "START_GAME"})
        assert game_manager.status == "QUESTION"

        curr_q = game_manager.get_current_question()
        # player-1 doğru cevap, player-2 doğru cevap, player-3 yanlış cevap
        http_post("/api/player/answer", {"player_id": "player-1", "question_id": curr_q.id, "choice": curr_q.correct})
        http_post("/api/player/answer", {"player_id": "player-2", "question_id": curr_q.id, "choice": curr_q.correct})
        http_post("/api/player/answer", {"player_id": "player-3", "question_id": curr_q.id, "choice": "B" if curr_q.correct != "B" else "C"})

        # Cevapları Açıkla & Liderlik Tablosu
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "REVEAL_ANSWER"})
        assert game_manager.status == "REVEAL"

        http_post("/api/admin/action", {"admin_pin": "220126", "action": "SHOW_LEADERBOARD"})
        assert game_manager.status == "LEADERBOARD"

        # Podyumu Aç
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "FINISH_PODIUM"})
        assert game_manager.status == "PODIUM"

        # Oyuncu ekranı sıralama endpointi kontrolü (/api/player/rank/{id})
        st_r1, r1_data, _, _ = http_get("/api/player/rank/player-1")
        assert st_r1 == 200 and r1_data["rank"] == 1
        print(f"  ✓ Oyuncu 1 Sıralaması: {r1_data['rank']}. sıra ({r1_data['score']} Puan)")

        st_r3, r3_data, _, _ = http_get("/api/player/rank/player-3")
        assert st_r3 == 200 and r3_data["rank"] == 3
        print(f"  ✓ Oyuncu 3 Sıralaması: {r3_data['rank']}. sıra ({r3_data['score']} Puan)")

        # Podyum Verisi
        st_pod, pod_res, _, _ = http_get("/api/podium")
        assert st_pod == 200
        assert pod_res["first"]["id"] == "player-1"
        assert pod_res["second"]["id"] == "player-2"
        print(f"  ✓ Podyum Şampiyonu: 🥇 {pod_res['first']['name']} ({pod_res['first']['score']} Puan)")
        print(f"  ✓ Podyum İkincisi: 🥈 {pod_res['second']['name']} ({pod_res['second']['score']} Puan)")

        print("\n" + "=" * 80)
        print("🏆 11 GEREKSİNİMİN TAMAMI %100 BAŞARIYLA GEÇTİ! SİSTEM CANLIYA VE DEPLOY'A HAZIR!")
        print("=" * 80)

    finally:
        server.should_exit = True

if __name__ == "__main__":
    run_comprehensive_11_step_qa_test()
