import os
import tempfile

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from spam_bot.services.link_scanner import find_dangerous_link
from spam_bot.services.nsfw_service import nsfw_service

# (chat_id, user_id) -> oxirgi tekshirilgan profil rasmining file_unique_id'i.
# Rasm o'zgarmagan bo'lsa qayta tahlil qilinmaydi (NudeNet ishga tushirilmaydi);
# foydalanuvchi rasmni almashtirsa, yangi file_unique_id kelib qayta tekshiriladi.
_last_checked_photo: dict[tuple[int, int], str] = {}


async def _scan_bio(bot: Bot, user_id: int) -> str | None:
    try:
        chat = await bot.get_chat(user_id)
    except TelegramBadRequest:
        return None
    bio = getattr(chat, "bio", None)
    if bio and find_dangerous_link(bio):
        return "malware_link"
    return None


async def _scan_photo(bot: Bot, chat_id: int, user_id: int) -> str | None:
    if not nsfw_service.available:
        return None
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
    except TelegramBadRequest:
        return None
    if photos.total_count == 0:
        return None

    photo = photos.photos[0][-1]
    cache_key = (chat_id, user_id)
    if _last_checked_photo.get(cache_key) == photo.file_unique_id:
        return None  # bu rasm avval tekshirilgan va toza topilgan edi
    _last_checked_photo[cache_key] = photo.file_unique_id

    try:
        file_info = await bot.get_file(photo.file_id)
    except TelegramBadRequest:
        return None

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await bot.download_file(file_info.file_path, tmp_path)
        if nsfw_service.is_explicit(tmp_path):
            return "nsfw_photo"
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Profil rasmini yuklab olishda xato ({user_id}): {exc}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return None


async def scan_user_profile(bot: Bot, chat_id: int, user_id: int) -> str | None:
    """Foydalanuvchi bio'si va profil rasmini tekshiradi.

    Har chaqirilganda ishlaydi (guruhga qo'shilganda ham, har xabarda ham) —
    aniq buzilish topilsa sababni ("malware_link" yoki "nsfw_photo"), aks
    holda None qaytaradi. Profil rasmi o'zgarmagan bo'lsa, uni qayta tahlil
    qilib o'tirmaydi (keshlanadi), shu bilan resurs tejaladi.
    """
    reason = await _scan_bio(bot, user_id)
    if reason:
        return reason
    return await _scan_photo(bot, chat_id, user_id)
