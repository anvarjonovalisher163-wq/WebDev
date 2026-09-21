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
from bot.models.referral import ReferralStatus
from bot.repositories.admin_repo import AdminRepo
from bot.repositories.channel_repo import ChannelRepo
from bot.repositories.invite_repo import InviteRepo
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.certificate_service import DEFAULT_ACCEPTANCE_TEXT
from bot.services.invite_service import InviteService
from bot.states.user_states import CertificateStates

router = Router(name="user_channel_events")

_JOINED_STATUSES = {"member", "administrator", "creator"}
_LEFT_STATUSES = {"left", "kicked"}


async def _notify_referrer_about_left_channel(
    event: ChatMemberUpdated, session: AsyncSession, bot: Bot
) -> None:
    """Taklif qilingan foydalanuvchi majburiy kanaldan chiqib ketishi bilan
    (chat_member hodisasi orqali) DARHOL aniqlanadi: uning tasdiqlangan
    referali bekor qilinadi va referrerga bir zumda xabar yuboriladi -
    endi buni bilish uchun yangi referral yoki "Mening takliflarim"ni
    kutish shart emas."""
    channels = await ChannelRepo(session).list_active()
    if event.chat.id not in {channel.chat_id for channel in channels}:
        return

    user_repo = UserRepo(session)
    left_user = await user_repo.get_by_tg_id(event.new_chat_member.user.id)
    if left_user is None:
        return

    referral_repo = ReferralRepo(session)
    referral = await referral_repo.get_by_referred_id(left_user.id)
    if referral is None or referral.status != ReferralStatus.APPROVED:
        return  # PENDING/allaqachon chiqib ketgan/bekor qilingan - hisobga olinmagan edi

    await referral_repo.mark_left_channels(referral)
    await session.commit()

    referrer = await user_repo.get_by_id(referral.referrer_id)
    if referrer is None:
        return

    settings = await SettingsRepo(session).get()
    approved = await referral_repo.count_by_referrer_and_status_in_season(
        referrer.id, ReferralStatus.APPROVED, referral.season_id
    )
    left_user_name = left_user.first_name or left_user.username or "Foydalanuvchi"
    notice = (
        f"⚠️ Siz taklif qilgan {left_user_name} majburiy kanal(lar)dan chiqib ketdi, "
        "shuning uchun bu taklif endi hisoblanmaydi.\n\n"
        f"Joriy tasdiqlangan takliflaringiz: {approved}/{settings.required_referral_count}."
    )

    try:
        await bot.send_message(referrer.tg_id, notice)
    except TelegramForbiddenError:
        referrer.is_blocked = True
        await session.commit()
    except TelegramBadRequest:
        pass


@router.chat_member()
async def on_private_channel_join(
    event: ChatMemberUpdated, session: AsyncSession, bot: Bot, state: FSMContext
) -> None:
    if event.new_chat_member.status in _LEFT_STATUSES and event.old_chat_member.status in _JOINED_STATUSES:
        await _notify_referrer_about_left_channel(event, session, bot)
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
