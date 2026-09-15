from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.invite_link import InviteLinkStatus
from bot.repositories.invite_repo import InviteRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.invite_service import InviteService

router = Router(name="user_channel_events")

_JOINED_STATUSES = {"member", "administrator", "creator"}
_LEFT_STATUSES = {"left", "kicked"}


@router.chat_member()
async def on_private_channel_join(event: ChatMemberUpdated, session: AsyncSession, bot: Bot) -> None:
    settings = await SettingsRepo(session).get()
    if settings.secret_channel_id is None or event.chat.id != settings.secret_channel_id:
        return

    if event.new_chat_member.status not in _JOINED_STATUSES:
        return
    if event.old_chat_member.status not in _LEFT_STATUSES:
        return  # allaqachon a'zo bo'lgan, yangi qo'shilish emas

    if event.invite_link is None:
        return

    invite_repo = InviteRepo(session)
    link = await invite_repo.get_by_link(event.invite_link.invite_link)
    if link is None or link.status != InviteLinkStatus.ACTIVE:
        return

    user_repo = UserRepo(session)
    user = await user_repo.get_by_id(link.user_id)
    if user is None or user.tg_id != event.new_chat_member.user.id:
        return  # havola boshqa foydalanuvchi tomonidan ishlatilgan - hisobga olinmaydi

    user.joined_private_channel = True
    user.joined_private_channel_at = datetime.now(timezone.utc)

    invite_service = InviteService(session, bot)
    await invite_service.mark_used_and_revoke(link, settings)
    await session.commit()

    try:
        await bot.send_message(
            user.tg_id,
            "Tabriklaymiz! Siz muvaffaqiyatli ravishda yopiq kanalga qo'shildingiz.",
        )
    except (TelegramForbiddenError, TelegramBadRequest):
        pass
