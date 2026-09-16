import os
import tempfile

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from spam_bot.services.link_scanner import find_dangerous_link
from spam_bot.services.nsfw_service import nsfw_service

# Bitta jarayon davomida har bir (chat, user) juftligi faqat bir marta
# skanerlanadi — birinchi xabar tekshiruvi shu orqali amalga oshadi.
_scanned: set[tuple[int, int]] = set()


async def scan_user_profile(bot: Bot, user_id: int) -> str | None:
    """Foydalanuvchi bio'si va profil rasmini tekshiradi.

    Aniq buzilish topilsa sababni ("malware_link" yoki "nsfw_photo"),
    aks holda None qaytaradi.
    """
    try:
        chat = await bot.get_chat(user_id)
    except TelegramBadRequest:
        return None

    bio = getattr(chat, "bio", None)
    if bio and find_dangerous_link(bio):
        return "malware_link"

    if not nsfw_service.available:
        return None

    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
    except TelegramBadRequest:
        return None
    if photos.total_count == 0:
        return None

    file_id = photos.photos[0][-1].file_id
    try:
        file_info = await bot.get_file(file_id)
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


async def scan_first_message(bot: Bot, chat_id: int, user_id: int) -> str | None:
    key = (chat_id, user_id)
    if key in _scanned:
        return None
    _scanned.add(key)
    return await scan_user_profile(bot, user_id)
