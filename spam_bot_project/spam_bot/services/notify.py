from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup
from loguru import logger

from spam_bot.config import settings


async def notify_operators(bot: Bot, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    """Botni joylashtirgan operator(lar)ga shaxsiy xabar yuboradi."""
    for operator_id in settings.admin_id_list:
        try:
            await bot.send_message(operator_id, text, reply_markup=reply_markup)
        except TelegramForbiddenError:
            logger.warning(f"Operatorga xabar yuborib bo'lmadi (bloklangan?): {operator_id}")
