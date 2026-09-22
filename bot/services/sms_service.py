import time
from typing import Optional

import httpx
from loguru import logger

from bot.config import settings

ESKIZ_BASE_URL = "https://notify.eskiz.uz/api"

_token_cache: Optional[str] = None
_token_expires_at: float = 0.0


async def _get_token() -> Optional[str]:
    global _token_cache, _token_expires_at
    if _token_cache and time.time() < _token_expires_at:
        return _token_cache

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{ESKIZ_BASE_URL}/auth/login",
                data={"email": settings.eskiz_email, "password": settings.eskiz_password},
            )
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error(f"Eskiz.uz'ga ulanib bo'lmadi: {exc}")
        return None

    token = data.get("data", {}).get("token")
    if not token:
        logger.error(f"Eskiz.uz login xatosi: {data}")
        return None

    _token_cache = token
    _token_expires_at = time.time() + 25 * 24 * 3600  # ~25 kun (token ~30 kun amal qiladi)
    return token


async def send_otp_sms(phone: str, code: str) -> bool:
    """Telefon raqamga kirish kodini SMS orqali yuboradi (Eskiz.uz).
    Sozlanmagan yoki xatolik bo'lsa False qaytaradi."""
    if not settings.eskiz_configured:
        return False

    token = await _get_token()
    if not token:
        return False

    message = f"UCHQUN kirish kodi: {code}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{ESKIZ_BASE_URL}/message/sms/send",
                headers={"Authorization": f"Bearer {token}"},
                data={"mobile_phone": phone, "message": message, "from": "4546"},
            )
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error(f"SMS yuborib bo'lmadi ({phone}): {exc}")
        return False

    if data.get("status") not in ("waiting", "success", "ok"):
        logger.error(f"Eskiz.uz SMS yuborish xatosi ({phone}): {data}")
        return False
    return True
