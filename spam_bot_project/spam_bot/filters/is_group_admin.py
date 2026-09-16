from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Filter
from aiogram.types import Message

_ADMIN_STATUSES = {"administrator", "creator"}


class IsGroupAdmin(Filter):
    """Buyruq faqat guruh (yoki superguruh) va uni yuborgan shaxs admin bo'lsagina ishlaydi."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.chat.type not in ("group", "supergroup"):
            return False
        if message.from_user is None:
            return False
        try:
            member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        except TelegramBadRequest:
            return False
        return member.status in _ADMIN_STATUSES
