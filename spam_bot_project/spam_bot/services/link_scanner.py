import re

# Yuklab olinadigan binar fayl kengaytmalari (zararli dastur tarqatish uchun tez-tez ishlatiladi).
_DANGEROUS_EXTENSIONS = (".apk", ".exe", ".msi", ".scr", ".bat", ".jar", ".vbs", ".cmd")

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Ochiqdan-ochiq behayo kanal/link kalit so'zlari (linkning o'zida yoki yaqinidagi matnda).
_ADULT_LINK_HINTS = (
    "onlyfans",
    "porn",
    "xxx",
    "intim-xizmat",
    "seks-uchrashuv",
)


def find_dangerous_link(text: str) -> str | None:
    """Zararli dastur havolasi yoki ochiq-sochiq kanal havolasini aniqlaydi."""
    if not text:
        return None
    for url in _URL_RE.findall(text):
        lowered = url.lower()
        if lowered.endswith(_DANGEROUS_EXTENSIONS):
            return url
        if any(hint in lowered for hint in _ADULT_LINK_HINTS):
            return url
    return None
