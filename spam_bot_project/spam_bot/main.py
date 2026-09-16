import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from loguru import logger

from spam_bot.config import settings
from spam_bot.db.session import engine
from spam_bot.handlers import setup_routers
from spam_bot.handlers.user.moderation_pipeline import init_moderation
from spam_bot.jobs.scheduler import scheduler, setup_jobs
from spam_bot.middlewares.db import DbSessionMiddleware
from spam_bot.models.base import Base
from spam_bot.services.crypto_service import CryptoService
from spam_bot.utils.error_handler import register_error_handler
from spam_bot.utils.logging import setup_logging
from spam_bot.web import create_web_app


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run_web_app(crypto: CryptoService) -> None:
    app = create_web_app(crypto)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    logger.info(f"/setkey HTTPS shakli {settings.web_host}:{settings.web_port} portida ishga tushdi")


async def main() -> None:
    setup_logging()
    await init_db()

    crypto = CryptoService(settings.key_encryption_secret)
    init_moderation(crypto)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware())
    setup_routers(dp)
    register_error_handler(dp)

    await run_web_app(crypto)

    setup_jobs(bot)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Spam bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
