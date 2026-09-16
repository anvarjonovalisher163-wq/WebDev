from loguru import logger

from spam_bot.config import settings
from spam_bot.db.session import async_session_factory
from spam_bot.repositories.spam_log_repo import SpamLogRepo
from spam_bot.repositories.usage_repo import UsageRepo


async def purge_old_records_job() -> None:
    async with async_session_factory() as session:
        spam_removed = await SpamLogRepo(session).purge_older_than(settings.retention_days)
        usage_removed = await UsageRepo(session).purge_older_than(settings.retention_days)
        await session.commit()
        if spam_removed or usage_removed:
            logger.info(f"Tozalandi: {spam_removed} ta spam yozuvi, {usage_removed} ta foydalanish yozuvi")
