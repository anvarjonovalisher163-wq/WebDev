from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from spam_bot.config import settings


async def notify_operators(bot: Bot, text: str) -> None:
    """Botni joylashtirgan operator(lar)ga shaxsiy xabar yuboradi."""
    for operator_id in settings.admin_id_list:
        try:
            await bot.send_message(operator_id, text)
        except TelegramForbiddenError:
            logger.warning(f"Operatorga xabar yuborib bo'lmadi (bloklangan?): {operator_id}")
