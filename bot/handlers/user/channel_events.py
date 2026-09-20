from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings as app_settings
from bot.keyboards.user import main_reply_keyboard
from bot.models.invite_link import InviteLinkStatus
from bot.repositories.admin_repo import AdminRepo
from bot.repositories.invite_repo import InviteRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.certificate_service import DEFAULT_ACCEPTANCE_TEXT
from bot.services.invite_service import InviteService
from bot.states.user_states import CertificateStates

router = Router(name="user_channel_events")

_JOINED_STATUSES = {"member", "administrator", "creator"}
_LEFT_STATUSES = {"left", "kicked"}


@router.chat_member()
async def on_private_channel_join(
    event: ChatMemberUpdated, session: AsyncSession, bot: Bot, state: FSMContext
) -> None:
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
    await invite_service.mark_used_and_revoke(link)
    await session.commit()

    settings = await SettingsRepo(session).get()
    acceptance_text = (settings.acceptance_text or DEFAULT_ACCEPTANCE_TEXT).replace(
        "{ism}", user.first_name
    )

    try:
        await bot.send_message(user.tg_id, acceptance_text)
        await bot.send_message(
            user.tg_id,
            "Sertifikatingizni rasmiylashtirish uchun to'liq ism va familiyangizni yuboring "
            "(masalan: Anvar Anvarov):",
        )
        if settings.marra_url:
            is_admin = await AdminRepo(session).get_by_tg_id(user.tg_id) is not None
            keyboard = main_reply_keyboard(app_settings.webapp_url, is_admin, marra_enabled=True)
            if keyboard is not None:
                await bot.send_message(
                    user.tg_id, "📖 Sizga yangi imkoniyat ochildi: Marra!", reply_markup=keyboard
                )
    except (TelegramForbiddenError, TelegramBadRequest):
        return

    # Foydalanuvchining bot bilan SHAXSIY suhbatidagi FSM holatini o'rnatamiz -
    # bu hodisa (chat_member) kanal chatiga tegishli bo'lgani uchun standart
    # `state` konteksti noto'g'ri chatga qarab turadi.
    private_key = StorageKey(bot_id=bot.id, chat_id=user.tg_id, user_id=user.tg_id)
    await FSMContext(storage=state.storage, key=private_key).set_state(
        CertificateStates.waiting_full_name
    )
