import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

from bot.config import settings
from bot.db.session import async_session_factory
from bot.handlers import setup_routers
from bot.jobs.scheduler import scheduler, setup_jobs
from bot.middlewares.db import DbSessionMiddleware
from bot.repositories.admin_repo import AdminRepo
from bot.utils.logging import setup_logging


async def main() -> None:
    setup_logging()

    async with async_session_factory() as session:
        await AdminRepo(session).ensure_super_admins(settings.super_admin_id_list)
        await session.commit()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())
    setup_routers(dp)

    bot_info = await bot.get_me()
    dp["bot_username"] = bot_info.username

    setup_jobs(bot)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
