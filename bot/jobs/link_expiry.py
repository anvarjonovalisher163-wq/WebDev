from aiogram import Bot
from loguru import logger

from bot.db.session import async_session_factory
from bot.services.invite_service import InviteService


async def expire_stale_links_job(bot: Bot) -> None:
    async with async_session_factory() as session:
        invite_service = InviteService(session, bot)
        count = await invite_service.expire_stale_links()
        await session.commit()
        if count:
            logger.info(f"{count} ta muddati o'tgan taklif havolasi bekor qilindi")
