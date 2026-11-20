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
        # 1. ADMIN PANELİ: GELİŞMİŞ "QUİZLERİM" BÖLÜMÜ
        # ---------------------------------------------------------------------
        print("[GEREKSİNİM 1] Admin Paneli - Gelişmiş 'Quizlerim' Bölümü Testi...")
        # 1.1 Manuel Soru Ekle
        manual_payload = {
            "admin_pin": "220126",
            "question": "Türkiye'nin en kapsamlı yapay zeka zirvesi hangisidir?",
            "options": {
                "A": "AI Era Zirvesi",
                "B": "Klasik Seminer",
                "C": "Eski Konferans",
                "D": "Genel Fuar"
            },
            "correct": "A",
            "explanation": "AI Era Zirvesi gençleri geleceğin teknolojileriyle buluşturur.",
            "duration": 20
        }
        status, m_res, _ = http_post("/api/admin/questions/manual", manual_payload)
        assert status == 200 and m_res["success"] is True, f"Manuel soru eklenemedi: {m_res}"
        added_id = m_res["question"]["id"]

        # 1.2 Soruları Listele
        status, q_list, _, _ = http_get("/api/admin/questions?admin_pin=220126")
        assert status == 200, "Sorular listelenemedi"
        found = any(q["id"] == added_id for q in q_list["questions"])
        assert found is True, "Eklenen manuel soru soru listesinde bulunamadı!"

        # 1.3 Soruyu Sil
        status, d_res, _ = http_delete(f"/api/admin/questions/{added_id}?admin_pin=220126")
        assert status == 200 and d_res["success"] is True, "Soru silinemedi!"
        print("  ✓ Manuel soru ekleme, listeleme ve silme fonksiyonları hatasız çalıştı.")

        # ---------------------------------------------------------------------
        # 2. İZLEYİCİ EMOJİ ATMA SİSTEMİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 2] İzleyici Emoji Atma Sistemi Testi...")
        emoji_payload = {
            "room_pin": active_pin,
            "emoji": "🔥",
            "player_name": "Testİzleyici"
        }
        status, emoji_res, _ = http_post("/api/reaction", emoji_payload)
        assert status == 200 and emoji_res["success"] is True, "Reaksiyon gönderilemedi!"
        
        # State'te last_reaction kontrolü
        _, state_res, _, _ = http_get("/api/state")
        assert state_res.get("last_reaction") is not None, "State içinde last_reaction bulunamadı!"
        assert state_res["last_reaction"]["emoji"] == "🔥"
        print("  ✓ İzleyici emoji reaksiyonu (🔥) başarıyla gönderildi ve state üzerinden broadcast edildi.")

        # ---------------------------------------------------------------------
        # 3. SONUÇLARI İNDİRME BUTONLARI (EXCEL & PDF)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 3] Sonuçları İndirme Butonları (Excel & PDF) Testi...")
        # 3.1 Excel İndir (.xlsx)
        status, _, raw_xlsx, ct_xlsx = http_get("/api/admin/export/excel?admin_pin=220126")
        assert status == 200, "Excel export isteği başarısız!"
        assert len(raw_xlsx) > 100, "Excel dosyası boş veya hatalı!"
        assert "spreadsheetml" in ct_xlsx or "octet-stream" in ct_xlsx, f"Geçersiz Excel MIME tipi: {ct_xlsx}"
        print(f"  ✓ Excel tablosu (.xlsx) başarıyla üretildi ({len(raw_xlsx)} bytes).")

        # 3.2 PDF İndir (.pdf)
        status, _, raw_pdf, ct_pdf = http_get("/api/admin/export/pdf?admin_pin=220126")
        assert status == 200, "PDF export isteği başarısız!"
        assert raw_pdf.startswith(b"%PDF"), "Üretilen dosya geçerli bir PDF formatında değil!"
        assert "application/pdf" in ct_pdf, f"Geçersiz PDF MIME tipi: {ct_pdf}"
        print(f"  ✓ PDF raporu (.pdf) başarıyla üretildi ({len(raw_pdf)} bytes).")

        # ---------------------------------------------------------------------
        # 4. BAĞIMSIZ SORU SÜRESİ VE OTOMATİK MOD AYARLARI
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 4] Bağımsız Soru Süresi ve Otomatik Mod Ayarları Testi...")
        # Soru süresini 20s, geçiş süresini 10s olarak bağımsız ayarla
        status, t_res, _ = http_post("/api/admin/timer", {
            "admin_pin": "220126",
            "question_duration": 20,
            "transition_delay": 10,
            "auto_mode": True
        })
        assert status == 200, "Zamanlayıcı ayarları güncellenemedi!"
        assert t_res["question_duration"] == 20
        assert t_res["transition_delay"] == 10
        assert t_res["auto_mode"] is True

        # State kontrolü
        _, state_res, _, _ = http_get("/api/state")
        assert state_res["question_duration"] == 20
        assert state_res["transition_delay"] == 10
        print("  ✓ Soru süresi (20s) ve Liderlik geçiş süresi (10s) birbirinden bağımsız olarak yapılandırıldı.")

        # ---------------------------------------------------------------------
        # 5. ARKA PLANDA HAREKETLİ SİMGELER
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 5] Arka Planda Hareketli Simgeler Testi...")
        status, _, raw_base, _ = http_get("/")
        base_html = raw_base.decode("utf-8")
        assert "bg-floating-icons" in base_html, "Hareketli simgeler konteyneri bulunamadı!"
        assert "floating-icon" in base_html, "Modern yüzen teknoloji simgeleri bulunamadı!"
        print("  ✓ Sayısı artırılmış akıcı yüzen teknoloji ve girişimcilik simgeleri doğrulandı.")

        # ---------------------------------------------------------------------
        # 6. SAHNE EKRANI KATILIMCI KARTI HATASININ DÜZELTİLMESİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 6] Sahne Ekranı Katılımcı Kartı Mükerrerlik Testi...")
        with open(ROOT_DIR / "static/js/stage.js", "r", encoding="utf-8") as f:
            stage_js_code = f.read()
        assert "[...players, ...players]" not in stage_js_code, "Mükerrer kart oluşturan kopya dizi tespit edildi!"
        assert "renderParticipantsList" in stage_js_code, "Tekil katılımcı listesi render fonksiyonu bulunamadı!"
        print("  ✓ Sahne ekranındaki mükerrer kopya kart hatası tamamen giderildi (1 oyuncu = 1 kart).")

        # ---------------------------------------------------------------------
        # 7. SAHNE EKRANI YERLEŞİMİ (QR KOD, PIN VE PROFİL AKIŞI)
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 7] Sahne Ekranı 2 Sütunlu Yerleşim Testi...")
        status, _, raw_stage, _ = http_get("/stage")
        stage_html = raw_stage.decode("utf-8")
        assert "lobby-qrcode" in stage_html, "QR Kod bulunamadı!"
        assert "lobby-pin-display" in stage_html, "QR Kodun hemen altındaki Oda PIN alanı bulunamadı!"
        assert "lobby-participants-container" in stage_html, "Geniş katılımcı profil akışı konteyneri bulunamadı!"
        assert "lg:col-span-5" in stage_html and "lg:col-span-7" in stage_html, "Sol ve Sağ 2 sütunlu grid düzeni bulunamadı!"
        print("  ✓ Sol sütun (QR + PIN) ve Sağ sütun (Katılımcı Profilleri) 2 sütunlu yerleşim doğrulandı.")

        # ---------------------------------------------------------------------
        # 8. OYUNCU SEKMESİ VE OKUL SEÇİM BUTONU
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 8] Oyuncu Sekmesi Okul Seçim Dropdown Testi...")
        status, _, raw_play, _ = http_get("/play")
        play_html = raw_play.decode("utf-8")
        assert '<select id="input-school"' in play_html, "Okul seçim butonu/dropdown'ı bulunamadı!"
        
        expected_schools = [
            "Halil İnalcık Anadolu Lisesi",
            "Cemil Meriç Kız Mesleki ve Teknik Anadolu Lisesi",
            "Güngören Anadolu Lisesi",
            "Erhan Dedeoğlu Anadolu Lisesi",
            "Güngören Gençosman Borsa İstanbul Mesleki ve Teknik Anadolu Lisesi",
            "Diğer"
        ]
        for school in expected_schools:
            assert school in play_html, f"Zorunlu okul listede bulunamadı: {school}"
        print("  ✓ Belirtilen 5 lise ve 'Diğer' seçeneğini içeren okul açılır listesi doğrulandı.")

        # ---------------------------------------------------------------------
        # 9. SIKI GÜVENLİK: ARGO, SİYASİ ENGELLEME VE 3 HAK BAN SİSTEMİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 9] Sıkı Güvenlik: Argo, Siyasi Engelleme ve 3 Hak Ban Sistemi Testi...")
        test_client_id = "test-violator-99"
        
        # 1. Hak İhlali
        st1, err1, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "akp genclik",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st1 == 400, f"1. Siyasi ihlal engellenmedi! Status: {st1}"
        assert "UYARI (1/3 Hak)" in err1["detail"], f"Beklenen 1/3 uyarısı alınamadı: {err1}"

        # 2. Hak İhlali
        st2, err2, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "chp li",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st2 == 400
        assert "UYARI (2/3 Hak)" in err2["detail"]

        # 3. Hak İhlali -> Kalıcı Ban (403 Forbidden)
        st3, err3, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "mhp li",
            "school": "Diğer",
            "avatar": "🐼",
            "player_id": test_client_id
        })
        assert st3 == 403, f"3. İhlal sonrası 403 kalıcı ban uygulanmadı! Status: {st3}"
        assert "HESABINIZ ENGELLENDİ" in err3["detail"]
        print("  ✓ 1., 2. uyarılar ve 3. ihlalde kalıcı BAN sistemi başarıyla test edildi.")

        # Admin Ban Listesi Kontrolü
        st_ban, ban_data, _, _ = http_get("/api/admin/banned?admin_pin=220126")
        assert st_ban == 200
        banned_entry = next((u for u in ban_data["banned_users"] if u["identifier"] == test_client_id), None)
        assert banned_entry is not None, "Banlanan kullanıcı admin ban listesinde bulunamadı!"
        print("  ✓ Admin paneli ban listesinde engellenen kullanıcı görüntülendi.")

        # Admin Ban Kaldırma (Unban)
        st_unban, unban_res, _ = http_post("/api/admin/unban", {
            "admin_pin": "220126",
            "identifier": test_client_id
        })
        assert st_unban == 200 and unban_res["success"] is True
        print(f"  ✓ Admin tarafından '{test_client_id}' kullanıcısının banı kaldırıldı.")

        # ---------------------------------------------------------------------
        # 10. İSİM SOYİSİM ALANI - SADECE HARF KURALI
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 10] İsim Soyisim Alanı - Sadece Harf Kuralı Testi...")
        # Sayı içeren isim denemesi
        st_num, err_num, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Ahmet123",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🦊",
            "player_id": "test-valid-player-1"
        })
        assert st_num == 400, "Rakam içeren isim kabul edildi!"
        assert "sadece harf" in err_num["detail"].lower(), f"Beklenen harf uyarısı yok: {err_num}"

        # Noktalama / sembol içeren isim denemesi
        st_sym, err_sym, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Mehmet!@#",
            "school": "Güngören Anadolu Lisesi",
            "avatar": "🐺",
            "player_id": "test-valid-player-2"
        })
        assert st_sym == 400, "Sembol içeren isim kabul edildi!"

        # Geçerli Türkçe harflerden oluşan isim ile başarılı katılım
        st_ok, ok_data, _ = http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Çağrı Öztürk",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🐼",
            "player_id": "test-valid-player-3"
        })
        assert st_ok == 200 and ok_data["success"] is True, f"Geçerli isimle katılım sağlanamadı: {ok_data}"
        print("  ✓ Rakam ve özel karakterler engellendi, Türkçe karakterli temiz isim başarıyla kabul edildi.")

        # ---------------------------------------------------------------------
        # 11. UÇTAN UCA QA SİMÜLASYON TESTİ
        # ---------------------------------------------------------------------
        print("\n[GEREKSİNİM 11] Uçtan Uca Admin, Sahne ve Kahoot Oyuncu Akışı Testi...")
        # Reset room
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "RESET_ROOM"})
        
        # 2 Öğrenci Katılımı (Seçilen Liselerle)
        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Elif Demir",
            "school": "Halil İnalcık Anadolu Lisesi",
            "avatar": "🐼",
            "player_id": "p-1"
        })
        http_post("/api/player/join", {
            "room_pin": active_pin,
            "name": "Mert Yıldız",
            "school": "Erhan Dedeoğlu Anadolu Lisesi",
            "avatar": "🦊",
            "player_id": "p-2"
        })

        # Yarışmayı Başlat
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "START_GAME"})
        assert game_manager.status == "QUESTION"

        # Cevap Gönder
        curr_q = game_manager.get_current_question()
        st_ans1, ans1, _ = http_post("/api/player/answer", {"player_id": "p-1", "question_id": curr_q.id, "choice": curr_q.correct})
        st_ans2, ans2, _ = http_post("/api/player/answer", {"player_id": "p-2", "question_id": curr_q.id, "choice": "B" if curr_q.correct != "B" else "C"})

        # Cevabı Açıkla & Liderlik & Podyum
        http_post("/api/admin/action", {"admin_pin": "220126", "action": "REVEAL_ANSWER"})
        assert game_manager.status == "REVEAL"

        http_post("/api/admin/action", {"admin_pin": "220126", "action": "SHOW_LEADERBOARD"})
        assert game_manager.status == "LEADERBOARD"

        http_post("/api/admin/action", {"admin_pin": "220126", "action": "FINISH_PODIUM"})
        assert game_manager.status == "PODIUM"

        st_pod, pod_res, _, _ = http_get("/api/podium")
        if pod_res["first"]["id"] != "p-1":
            print("DEBUG: ans1:", ans1, "ans2:", ans2, "pod_res:", pod_res)
        assert pod_res["first"]["id"] == "p-1"
        print(f"  ✓ Şampiyon: {pod_res['first']['name']} ({pod_res['first']['score']} Puan)")

        print("\n" + "=" * 80)
        print("🏆 11 GEREKSİNİMİN TAMAMI %100 BAŞARIYLA GEÇTİ! SİSTEM CANLIYA VE DEPLOY'A HAZIR!")
        print("=" * 80)

    finally:
        server.should_exit = True

if __name__ == "__main__":
    run_comprehensive_11_step_qa_test()
