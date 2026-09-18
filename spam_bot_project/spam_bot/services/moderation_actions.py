from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatPermissions
from loguru import logger

from spam_bot.services.ban_tracker import mark_banned

MUTE_HOURS = 24

_NO_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

_FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def delete_message_safe(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest as exc:
        logger.debug(f"Xabarni o'chirib bo'lmadi ({chat_id}/{message_id}): {exc}")


def mute_until() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=MUTE_HOURS)


async def mute_user(bot: Bot, chat_id: int, user_id: int, until: datetime) -> bool:
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions=_NO_PERMISSIONS, until_date=until)
        return True
    except TelegramBadRequest as exc:
        logger.warning(f"Foydalanuvchini ovozsizlantirib bo'lmadi ({chat_id}/{user_id}): {exc}")
        return False


async def unmute_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions=_FULL_PERMISSIONS)
        return True
    except TelegramBadRequest as exc:
        logger.warning(f"Foydalanuvchi ovozini yoqib bo'lmadi ({chat_id}/{user_id}): {exc}")
        return False


async def ban_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        await bot.ban_chat_member(chat_id, user_id)
        mark_banned(chat_id, user_id)
        return True
    except TelegramBadRequest as exc:
        logger.warning(f"Foydalanuvchini bloklab bo'lmadi ({chat_id}/{user_id}): {exc}")
        return False


async def unban_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        return True
    except TelegramBadRequest as exc:
        logger.warning(f"Foydalanuvchini blokdan chiqarib bo'lmadi ({chat_id}/{user_id}): {exc}")
        return False
