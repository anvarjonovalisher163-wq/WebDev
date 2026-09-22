from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from loguru import logger

from bot.db.session import async_session_factory
from bot.repositories.user_repo import UserRepo
from bot.services.invite_service import InviteService

EXPIRED_LINK_NOTICE = (
    "⏰ Sizga berilgan maxfiy havolaning muddati tugadi (siz vaqtida "
    "qo'shilmagansiz).\n\n"
    "\"📊 Mening takliflarim\" tugmasini qayta bosing - sizga darhol yangi "
    "havola beriladi."
)


async def expire_stale_links_job(bot: Bot) -> None:
    async with async_session_factory() as session:
        invite_service = InviteService(session, bot)
        expired_links = await invite_service.expire_stale_links()
        await session.commit()
        if not expired_links:
            return

        logger.info(f"{len(expired_links)} ta muddati o'tgan taklif havolasi bekor qilindi")

        # Havola bekor bo'lganini foydalanuvchiga o'zi aytadi - aks holda u
        # nega hech narsa bo'lmayotganini bilmay, qayta urinib ko'rmay qoladi.
        user_repo = UserRepo(session)
        for link in expired_links:
            user = await user_repo.get_by_id(link.user_id)
            if user is None or user.joined_private_channel or user.is_blocked:
                continue
            try:
                await bot.send_message(user.tg_id, EXPIRED_LINK_NOTICE)
            except (TelegramForbiddenError, TelegramBadRequest):
                continue
