import re
import time
from typing import Dict, List, Optional, Tuple

# Comprehensive Bad Words & Political Terminology Blacklist
FORBIDDEN_TERMS = {
    # Profanity, insults, slang
    "amk", "aq", "oç", "piç", "sik", "siktir", "sikeyim", "yarrak", "yarak", "göt", "ibne",
    "orospu", "kaltak", "fahişe", "kahpe", "pezevenk", "puşt", "dalyarak", "amcık", "taşak",
    "meme", "götlek", "dangalak", "gerizekalı", "aptal", "salak", "ahmak", "bok", "it",
    # Political parties, leaders, acronyms and slang derivatives
    "akp", "akparti", "akpli", "chp", "chpli", "mhp", "mhpli", "hdp", "hdpli", "dem", "demparti", "demli",
    "iyiparti", "tip", "tipli", "zaferpartisi", "hudapar", "deva", "gelecekpartisi", "refah", "saadet",
    "binali", "kılıçdaroğlu", "kilicdaroglu", "kemal", "kemalist",
    "erdoğan", "erdogan", "tayyip", "rte", "rtesi", "reis",
    "bahçeli", "bahceli", "özgürözel", "ozgurozel", "imamoğlu", "imamoglu",
    "yavaş", "mansuryavas", "demirtas", "demirtaş", "selo", "selocan",
    "öcalan", "ocalan", "apo", "aposi", "apocu", "apoist",
    "pkk", "pkkli", "ypg", "ypgli", "pyd", "pydli",
    "fetö", "feto", "fetocu", "fetullah", "dhkpc", "hizbullah",
    "komünist", "faşist", "terörist", "darbe", "darbeci", "bozkurt", "ülkücü", "ulkucu"
}

# Exact political/slang tokens and party variations
POLITICAL_ACRONYMS = {
    "akp", "akpli", "akparti", "chp", "chpli", "mhp", "mhpli",
    "hdp", "hdpli", "dem", "demli", "demparti", "tip", "tipli",
    "pkk", "pkkli", "ypg", "ypgli", "pyd", "pydli", "fetö", "feto", "fetocu",
    "dhkpc", "hizbullah", "apo", "aposi", "apocu", "apoist",
    "rte", "rtesi", "reis", "tayyip", "selo", "selocan"
}

# Substring terms (safe distinct terms that do not collide with common Turkish names like Demir)
SUBSTRING_TERMS = {
    "orospu", "pezevenk", "siktir", "sikeyim", "yarrak", "yarak", "amcık", "dalyarak",
    "kaltak", "fahişe", "puşt", "kılıçdaroğlu", "kilicdaroglu", "erdoğan", "erdogan",
    "bahçeli", "bahceli", "özgürözel", "ozgurozel", "imamoğlu", "imamoglu",
    "mansuryavas", "demirtaş", "demirtas", "öcalan", "ocalan", "terörist", "komünist", "faşist",
    "rtesi", "aposi", "fetocu", "fetullah", "darbeci"
}

# Troll & Gibberish Patterns (keyboard smash)
TROLL_PATTERNS = [
    r"asdasd", r"qweqwe", r"zxczxc", r"qwerty", r"sadasd", r"fghjkl",
    r"deneme", r"testtest", r"admin", r"anonim", r"misafir"
]

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
        2. Real Name and Surname validation: Must have at least First name and Last name (2 words).
           If violated -> friendly formatting warning, NO ban.
        3. Troll/Gibberish check (repeated sequences, keyboard smash) -> warning, NO ban.
        4. Bad words, profanity, and political party / figure derivatives ("rtesi", "aposi", etc.)
           If violated -> strict warning, 3 attempts limit -> permanent BAN.
        """
        if self.is_banned(identifier):
            return False, "Sistemden 3 kez uygunsuz kural ihlali yaptığınız için kalıcı olarak BANLANDINIZ!", {
                "banned": True
            }

        cleaned = name.strip()
        if not cleaned:
            return False, "Lütfen bir isim soyisim giriniz!", {"type": "empty"}

        # RULE 1: Sadece Harf Kuralı (Only Letters and spaces allowed)
        if not re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ\s]+$', cleaned):
            return False, "İsim Soyisim sadece harflerden oluşmalıdır! Sayı, rakam veya özel karakter kullanmayınız.", {
                "type": "invalid_chars",
                "is_letter_error": True
            }

        # RULE 2: Gerçek Ad ve Soyad Doğrulaması (En az 2 kelime, her biri en az 2 harf)
        words = cleaned.split()
        if len(words) < 2:
            return False, "Lütfen geçerli bir Ad ve Soyad giriniz (Örn: Ahmet Yılmaz).", {
                "type": "incomplete_name",
                "is_formatting_error": True
            }

        for w in words:
            if len(w) < 2:
                return False, "Ad ve soyadınızın her bir parçası en az 2 harften oluşmalıdır.", {
                    "type": "too_short_word",
                    "is_formatting_error": True
                }

        # RULE 3: Anlamsız Harf Tekrarı ve Troll Giriş Kontrolü
        cleaned_lower = cleaned.lower()
        if re.search(r'(.)\1{3,}', cleaned_lower): # 4 or more same character in a row
            return False, "Lütfen gerçek bir Ad Soyad giriniz (Tekrarlayan sahte karakterler tespit edildi).", {
                "type": "troll_name",
                "is_formatting_error": True
            }

        for pattern in TROLL_PATTERNS:
            if pattern in cleaned_lower:
                return False, "Lütfen gerçek bir Ad Soyad giriniz (Geçersiz isim yapısı).", {
                    "type": "troll_name",
                    "is_formatting_error": True
                }

        # RULE 4: Argo, Küfür ve Siyasi İsim Engellemesi (Siyasi Kısaltmalar: "rtesi", "aposi" vb.)
        normalized = normalize_text_for_filter(cleaned)
        contains_forbidden = False
        matched_term = ""

        # Check individual words (Exact match or political acronym)
        for w in words:
            norm_w = normalize_text_for_filter(w)
            if norm_w in POLITICAL_ACRONYMS or norm_w in FORBIDDEN_TERMS:
                contains_forbidden = True
                matched_term = w
                break

        # Check distinct substring terms (like specific profanities, political leaders and political suffixes)
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
                    "reason": f"3 kez kural ihlali (Yasaklı/Siyasi terim: '{matched_term}')",
                    "banned_at": time.time(),
                    "attempts": current_violations
                }
                return False, f"HESABINIZ ENGELLENDİ: 3 kez yasaklı/siyasi içerik denediğiniz için sistemden süresiz banlandınız! (İhlal: {matched_term})", {
                    "banned": True,
                    "attempts": current_violations
                }
            else:
                remaining = 3 - current_violations
                return False, f"UYARI ({current_violations}/3 Hak): Argo, küfür veya siyasi isim/kısaltma kullanılamaz! Kalan hak: {remaining}. (3 ihlalde süresiz banlanırsınız)", {
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
