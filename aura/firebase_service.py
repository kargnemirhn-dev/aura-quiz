import logging
from typing import Optional, Dict, Any
from aura.config import settings

logger = logging.getLogger("aura.firebase")

_firestore_client = None
_firebase_initialized = False

def init_firebase() -> bool:
    global _firestore_client, _firebase_initialized
    if _firebase_initialized:
        return _firestore_client is not None

    if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred = credentials.Certificate({
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID or "key-id",
                    "private_key": settings.FIREBASE_PRIVATE_KEY,
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    "token_uri": "https://oauth2.googleapis.com/token",
                })
                firebase_admin.initialize_app(cred)
            _firestore_client = firestore.client()
            _firebase_initialized = True
            logger.info("Firebase Admin & Firestore successfully initialized!")
            return True
        except Exception as e:
            logger.warning(f"Could not initialize Firebase Admin SDK: {e}. Falling back to internal state.")
            _firebase_initialized = True
            _firestore_client = None
            return False
    else:
        logger.info("Firebase server credentials not detected. Running with in-memory & real-time API sync.")
        _firebase_initialized = True
        _firestore_client = None
        return False

def get_firestore_client():
    if not _firebase_initialized:
        init_firebase()
    return _firestore_client

def get_firebase_web_config() -> Dict[str, Any]:
    """
    Returns public web config for the browser Firestore client.
    Safe for frontend inclusion (does NOT contain private keys).
    """
    return {
        "enabled": bool(settings.FIREBASE_API_KEY and settings.FIREBASE_PROJECT_ID),
        "apiKey": settings.FIREBASE_API_KEY,
        "authDomain": settings.FIREBASE_AUTH_DOMAIN or f"{settings.FIREBASE_PROJECT_ID}.firebaseapp.com",
        "projectId": settings.FIREBASE_PROJECT_ID,
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET or f"{settings.FIREBASE_PROJECT_ID}.appspot.com",
        "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
        "appId": settings.FIREBASE_APP_ID
    }

async def sync_game_state_to_firestore(room_pin: str, state_dict: Dict[str, Any]):
    """Syncs state to Firestore document if available"""
    client = get_firestore_client()
    if client:
        try:
            doc_ref = client.collection("rooms").document(room_pin)
            doc_ref.set(state_dict, merge=True)
        except Exception as e:
            logger.warning(f"Failed to sync state to Firestore: {e}")

async def sync_player_to_firestore(room_pin: str, player_id: str, player_dict: Dict[str, Any]):
    """Syncs player to Firestore subcollection if available"""
    client = get_firestore_client()
    if client:
        try:
            doc_ref = client.collection("rooms").document(room_pin).collection("players").document(player_id)
            doc_ref.set(player_dict, merge=True)
        except Exception as e:
            logger.warning(f"Failed to sync player to Firestore: {e}")
