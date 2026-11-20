# 🚀 AI ERA: TEKNOLOJİ & GİRİŞİMCİLİK ZİRVESİ
## Aura Bilgi Yarışması (Python & Firebase & Gemini AI)

Next.js yerine **Python (FastAPI)** altyapısıyla sıfırdan, yüksek performanslı, hatasız ve production-ready olarak geliştirilmiş gerçek zamanlı Kahoot tarzı bilgi yarışması platformu.

---

## 🌟 Öne Çıkan Özellikler & Mimari

### 1. 🐍 Python & FastAPI Altyapısı
- **Asenkron ve Hafif:** Python 3.12 + FastAPI ile gerçek zamanlı reaktif yapı.
- **Vercel Serverless Ready:** `api/index.py` ve `vercel.json` ile Vercel üzerinde sıfır konfigürasyon hatasıyla çalışır.
- **Çift Modlu Veri Senkronizasyonu:**
  - **Firebase Firestore:** Hem sunucu hem tarayıcı tarafı canlı dinleyici (`onSnapshot`).
  - **SSE (Server-Sent Events) Fallback:** Firebase anahtarları girilmese dahi yerel ortamda anında sıfır gecikmeli gerçek zamanlı senkronizasyon.

### 2. 🤖 Gemini AI Soru Üretimi (30 Özgün Soru)
- Google Gemini API entegrasyonu ile tek tıkla zirveye özel **30 adet taze, özgün ve dengeli** soru üretimi.
- Konular: Yapay Zeka (LLM'ler, Transformer, Ajanlar, Donanım), Girişimcilik (Unicornlar, Decacornlar, Yatırım Turları, MVP, Pitch Deck) ve Teknoloji Öncüleri.
- API anahtarı girilmese bile hazırda 30 soruluk özenle hazırlanmış zengin soru bankası.

### 3. 📱 Kahoot Tarzı Oyuncu Ekranı (`/play`)
- **Telefon Kuralı:** Kesinlikle soru metni ve şık yazıları telefonda görünmez.
- **Sadece 4 Kahoot Rengi ve Sembolü:**
  - 🔴 Kırmızı (🔺 Üçgen - A)
  - 🔷 Mavi (⏹️ Kare - B)
  - 🟡 Sarı (⏺️ Daire - C - `bg-yellow-500`)
  - 🟢 Yeşil (⭐️ Yıldız - D)
- **"Odadan Çık" Butonu:** Yarışmacının dilediği zaman odadan ayrılabilmesini ve oturumunu sıfırlayabilmesini sağlar.
- **Avatar Seçim Ekranı:** 12 farklı eğlenceli teknoloji/yapay zeka emojisi (`🚀`, `🤖`, `💡`, `⚡`, `🧠`, `🦄`, `🏆`, `🎯`, `🔥`, `👑`, `💻`, `🪐`).

### 4. 📺 Büyük Sahne Ekranı (`/stage`)
- **QR Kod Büyütme Modalı:** Salondaki uzak katılımcıların rahatça taraması için tek tıkla dev QR modalı açılır.
- **C Şıkkı Sarı Rengi:** Özel `bg-yellow-500` sınıfı ile kusursuz renk ayrımı.
- **Yatay Kayan Katılımcı Kartları:** Lobide bekleyen yarışmacıların avatarı, adı ve üniversitesi kayan şerit halinde akar.
- **3-2-1 Podyum Animasyonu:** Yarışma sonunda 3., 2. ve 1. için basamaklı 3D podyum yükselmesi, Web Audio zafer fanfarı ve konfeti patlaması (`canvas-confetti`).

### 5. ⏱️ Sayaçlar ve Otomatik Mod
- **Esnek Süreler:** 5s, 10s veya 15s ayarlanabilir soru süreleri.
- **Otomatik Akış Modu:** Soru bittiğinde otomatik cevap açıklama, liderlik tablosu ve sonraki soruya geçiş (sayaç kilitlenmesi veya memory leak olmadan).

---

## 📁 Proje Dizin Yapısı

```
aura_quiz/
├── api/
│   └── index.py            # Vercel Serverless Function giriş noktası
├── aura/
│   ├── __init__.py
│   ├── config.py           # .env ve ayar yönetimi
│   ├── models.py           # Pydantic veri modelleri
│   ├── gemini_service.py   # Gemini API 30 soru üretimi + soru bankası
│   ├── firebase_service.py # Firebase Admin SDK & Web Config
│   ├── game_manager.py     # Reaktif yarışma motoru & durum makinesi
│   └── routes.py           # FastAPI HTML sayfaları ve REST API'leri
├── templates/
│   ├── base.html           # Tailwind CDN, Lucide, Audio, Confetti
│   ├── index.html          # Giriş Portalı
│   ├── stage.html          # Sahne Ekranı (/stage)
│   ├── play.html           # Oyuncu Ekranı (/play)
│   └── admin.html          # Yönetici Paneli (/admin)
├── static/
│   ├── css/
│   │   └── style.css       # Kahoot butonları, podyum ve animasyonlar
│   └── js/
│       ├── audio.js        # Web Audio API ses motoru (0 dış bağımlılık)
│       ├── stage.js        # Sahne ekranı kontrolcüsü
│       ├── play.js         # Oyuncu mobil kontrolcüsü
│       └── admin.js        # Admin paneli kontrolcüsü
├── tests/
│   └── test_qa_simulation.py # Tam kapsamlı QA test simülatörü
├── .env.example            # Örnek çevre değişkenleri
├── .gitignore              # Git yok sayma listesi
├── requirements.txt        # Python paket bağımlılıkları
├── vercel.json             # Vercel yapılandırması
├── main.py                 # Yerel sunucu başlatma
└── README.md
```

---

## 🛠️ Kurulum ve Yerel Çalıştırma

### 1. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 2. Çevre Değişkenlerini Ayarlayın
`.env.example` dosyasını `.env` olarak kopyalayın:
```bash
cp .env.example .env
```
İsteğe bağlı olarak `ADMIN_PIN`, `GEMINI_API_KEY` ve Firebase bilgilerinizi girin. (Varsayılan Admin PIN: `1923`, Varsayılan Oda PIN: `2026`).

### 3. Sunucuyu Başlatın
```bash
python main.py
```
Sunucu açıldıktan sonra:
- **Giriş Portalı:** [http://localhost:8000/](http://localhost:8000/)
- **Sahne Ekranı:** [http://localhost:8000/stage](http://localhost:8000/stage)
- **Oyuncu Ekranı:** [http://localhost:8000/play](http://localhost:8000/play)
- **Yönetici Paneli:** [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🧪 Kendini Test Eden QA Simülasyonunu Çalıştırma

Tüm sistem fonksiyonlarını (Admin, Sahne ve Oyuncular) otomatik simüle eden test paketini çalıştırmak için:
```bash
python tests/test_qa_simulation.py
```

Test çıktısında 6 kritik aşamanın tamamı (%100) doğrulanır:
- Sayfa ve UI gereksinimleri (QR Modal, C-yellow `bg-yellow-500`, Marquee, Podyum, Oyuncu Kahoot butonları)
- Oda PIN sistemi ve Admin yetkilendirmesi
- Soru bankası (30 soru)
- Oyuncu katılımı, "Odadan Çık" ve cevap mekanizması
- 5s/10s/15s sayaçlar ve Otomatik Mod
- Tam yaşam döngüsü (Soru -> Cevap -> Reveal -> Liderlik -> Podyum 1., 2., 3.)

---

## 🐙 GitHub'a Gönderme ve Vercel'e Dağıtım (Deployment)

### GitHub'a Gönderme:
```bash
git init
git add .
git commit -m "feat: AI ERA Zirvesi Python altyapısı ve tam QA paketi"
git branch -M main
git remote add origin https://github.com/<KULLANICI_ADINIZ>/<DEPO_ADINIZ>.git
git push -u origin main
```

### Vercel'e Dağıtım:
1. [vercel.com](https://vercel.com) adresine gidin ve **Add New Project** seçeneğini seçin.
2. GitHub deponuzu içe aktarın (Import).
3. Vercel, `vercel.json` dosyasını otomatik algılayacaktır.
4. **Environment Variables** bölümüne şunları ekleyin:
   - `ADMIN_PIN`: (Örn: `1923`)
   - `DEFAULT_ROOM_PIN`: (Örn: `2026`)
   - `GEMINI_API_KEY`: (Google AI Studio'dan alınan anahtar)
   - *(İsteğe bağlı)* Firebase Firestore ortam değişkenleri
5. **Deploy** butonuna tıklayın. Saniyeler içinde canlıya alınacaktır!
