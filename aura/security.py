import re
import time
from typing import Dict, List, Optional, Tuple

# Comprehensive Bad Words & Political Terminology Blacklist (Normalized lowercase)
FORBIDDEN_TERMS = {
    # Profanity, insults, slang
    "amk", "aq", "oç", "piç", "sik", "siktir", "sikeyim", "yarrak", "yarak", "göt", "ibne",
    "orospu", "kaltak", "fahişe", "kahpe", "pezevenk", "puşt", "dalyarak", "amcık", "taşak",
    "meme", "götlek", "dangalak", "gerizekalı", "aptal", "salak", "ahmak", "bok", "it",
    # Political parties, abbreviations, political figures & illegal organizations
    "akp", "akparti", "chp", "mhp", "hdp", "dem", "demparti", "iyiparti", "tip", "zaferpartisi",
    "hudapar", "deva", "gelecekpartisi", "refah", "saadet", "binali", "kılıçdaroğlu", "kilicdaroglu",
    "erdoğan", "erdogan", "bahçeli", "bahceli", "özgürözel", "ozgurozel", "imamoğlu", "imamoglu",
    "yavaş", "mansuryavas", "demirtas", "demirtaş", "öcalan", "ocalan", "apo", "pkk", "ypg", "pyd",
    "fetö", "feto", "dhkpc", "hizbullah", "komünist", "faşist", "terörist", "darbe"
}

# Exact political/slang tokens and party variations
POLITICAL_ACRONYMS = {
    "akp", "akpli", "akparti", "chp", "chpli", "mhp", "mhpli",
    "hdp", "hdpli", "dem", "demli", "demparti", "tip", "tipli",
    "pkk", "pkkli", "ypg", "ypgli", "pyd", "pydli", "fetö", "feto", "fetocu",
    "dhkpc", "hizbullah", "apo", "apocu"
}

# Substring terms (safe distinct terms that do not collide with common Turkish names like Demir)
SUBSTRING_TERMS = {
    "orospu", "pezevenk", "siktir", "sikeyim", "yarrak", "yarak", "amcık", "dalyarak",
    "kaltak", "fahişe", "puşt", "kılıçdaroğlu", "kilicdaroglu", "erdoğan", "erdogan",
    "bahçeli", "bahceli", "özgürözel", "ozgurozel", "imamoğlu", "imamoglu",
    "mansuryavas", "demirtaş", "demirtas", "öcalan", "ocalan", "terörist", "komünist", "faşist"
}

def normalize_text_for_filter(text: str) -> str:
    """Normalizes Turkish text, removes repeated letters and leet-speak variations"""
    if not text:
        return ""
    t = text.lower().strip()
    replacements = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't',
        '@': 'a', '$': 's'
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    # Remove non-alphanumeric chars
    t = re.sub(r'[^a-z0-9]', '', t)
    # Compress repeated chars
    t = re.sub(r'(.)\1+', r'\1', t)
    return t

class SecurityService:
    def __init__(self):
        # Maps client_id / identifier -> violation count
        self.violation_counts: Dict[str, int] = {}
        # List of banned users: { "id": str, "name": str, "reason": str, "banned_at": float, "attempts": int }
        self.banned_users: Dict[str, Dict] = {}

    def is_banned(self, identifier: str) -> bool:
        return identifier in self.banned_users

    def validate_name(self, name: str, identifier: str) -> Tuple[bool, str, Dict]:
        """
        Validates player name according to Summit guidelines:
        1. Letter-only rule: Only Turkish/Latin letters & space allowed.
           If violated -> warning only, NO ban.
        2. Bad words & political filter:
           If violated -> warning, 3 attempts limit -> permanent BAN.
        """
        if self.is_banned(identifier):
            return False, "Sistemden 3 kez uygunsuz kural ihlali yaptığınız için kalıcı olarak BANLANDINIZ!", {
                "banned": True
            }

        cleaned = name.strip()
        if not cleaned:
            return False, "Lütfen bir isim soyisim giriniz!", {"type": "empty"}

        # RULE 1: Sadece Harf Kuralı (Only Letters and spaces allowed)
        # Allows Turkish chars: ç, Ç, ğ, Ğ, ı, İ, ö, Ö, ş, Ş, ü, Ü and Latin letters and space
        if not re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ\s]+$', cleaned):
            return False, "İsim Soyisim sadece harflerden oluşmalıdır! Sayı, rakam veya özel karakter kullanmayınız.", {
                "type": "invalid_chars",
                "is_letter_error": True
            }

        # RULE 2: Argo, Küfür ve Siyasi İsim Engellemesi
        normalized = normalize_text_for_filter(cleaned)
        contains_forbidden = False
        matched_term = ""

        # Check individual words (Exact match or political acronym)
        words = cleaned.lower().split()
        for w in words:
            norm_w = normalize_text_for_filter(w)
            if norm_w in POLITICAL_ACRONYMS or norm_w in FORBIDDEN_TERMS:
                contains_forbidden = True
                matched_term = w
                break

        # Check distinct substring terms (like specific profanities or full political names)
        if not contains_forbidden:
            for term in SUBSTRING_TERMS:
                norm_term = normalize_text_for_filter(term)
                if norm_term in normalized:
                    contains_forbidden = True
                    matched_term = term
                    break

        if contains_forbidden:
            current_violations = self.violation_counts.get(identifier, 0) + 1
            self.violation_counts[identifier] = current_violations

            if current_violations >= 3:
                # 3. İhlal -> Kalıcı Ban!
                self.banned_users[identifier] = {
                    "id": identifier,
                    "identifier": identifier,
                    "name": cleaned,
                    "last_attempt_name": cleaned,
                    "reason": f"3 kez kural ihlali (Yasaklı/Argo kelime: '{matched_term}')",
                    "banned_at": time.time(),
                    "attempts": current_violations
                }
                return False, f"HESABINIZ ENGELLENDİ: 3 kez yasaklı/siyasi içerik denediğiniz için sistemden süresiz banlandınız! (İhlal: {matched_term})", {
                    "banned": True,
                    "attempts": current_violations
                }
            else:
                remaining = 3 - current_violations
                return False, f"UYARI ({current_violations}/3 Hak): Argo, küfür veya siyasi isim kullanılamaz! Kalan hak: {remaining}. (3 ihlalde süresiz banlanırsınız)", {
                    "type": "bad_word",
                    "attempts": current_violations,
                    "remaining": remaining
                }

        return True, "Geçerli", {}

    def unban_user(self, identifier: str) -> bool:
        if identifier in self.banned_users:
            del self.banned_users[identifier]
            self.violation_counts[identifier] = 0
            return True
        return False

    def get_banned_list(self) -> List[Dict]:
        return list(self.banned_users.values())

security_service = SecurityService()
