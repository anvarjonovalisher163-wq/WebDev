from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from spam_bot.config import settings
from spam_bot.db.session import async_session_factory
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.repositories.spam_log_repo import SpamLogRepo


async def send_daily_report_job(bot: Bot) -> None:
    async with async_session_factory() as session:
        group_repo = GroupRepo(session)
        spam_repo = SpamLogRepo(session)
        enabled_groups = await group_repo.list_enabled()
        since = datetime.now(timezone.utc) - timedelta(days=1)
        spam_count = await spam_repo.count_total_since(since)

    text = (
        "🗓️ <b>Kunlik hisobot</b>\n"
        f"Faol guruhlar: {len(enabled_groups)}\n"
        f"So'nggi 24 soatda tutilgan spam: {spam_count}"
    )
    for operator_id in settings.admin_id_list:
        try:
            await bot.send_message(operator_id, text)
        except TelegramForbiddenError:
            logger.warning(f"Operatorga hisobot yuborib bo'lmadi (bloklangan?): {operator_id}")
