from aiogram.filters import Filter
from aiogram.types import Message

from spam_bot.config import settings


class IsOperator(Filter):
    """Botni joylashtirgan operator (ADMIN_TELEGRAM_IDS ro'yxatidagi shaxs)."""

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return message.from_user.id in settings.admin_id_list
