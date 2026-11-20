import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "AI ERA: TEKNOLOJİ & GİRİŞİMCİLİK ZİRVESİ"
    PROJECT_SUBTITLE: str = "Aura Bilgi Yarışması"
    VERSION: str = "2.0.0"

    # Security & Access Controls
    ADMIN_PIN: str = os.getenv("ADMIN_PIN", "220126")
    STAGE_PIN: str = os.getenv("STAGE_PIN", "220126")
    DEFAULT_ROOM_PIN: str = os.getenv("DEFAULT_ROOM_PIN", "")

    def set_admin_pin(self, new_pin: str):
        self.ADMIN_PIN = new_pin.strip()

    # Gemini AI API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Firebase Configuration (Optional in local mode, used for Firestore sync)
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_PRIVATE_KEY_ID: str = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")

    # Firebase Web Client Public Config (Safe for browser Firestore SDK)
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN: str = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    FIREBASE_MESSAGING_SENDER_ID: str = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
    FIREBASE_APP_ID: str = os.getenv("FIREBASE_APP_ID", "")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

settings = Settings()
