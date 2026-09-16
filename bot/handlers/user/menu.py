from typing import Optional

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user._common import check_gate
from bot.keyboards.user import (
    BTN_INVITE,
    BTN_MY_REFERRALS,
    CB_REFRESH_MY_REFERRALS,
    CB_SHOW_INVITE,
    my_referrals_refresh_keyboard,
    subscription_gate_keyboard,
)
from bot.models.settings import BotSettings
from bot.models.user import User
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.secret_link_flow import try_auto_grant_secret_link
from bot.services.subscription_service import SubscriptionService
from bot.services.user_service import build_referral_link

router = Router(name="user_menu")


async def require_ready_user(message: Message, session: AsyncSession, bot: Bot) -> Optional[User]:
    user = await UserRepo(session).get_by_tg_id(message.from_user.id)
    if user is None or user.is_blocked:
        await message.answer("Avval /start buyrug'ini yuboring.")
        return None

    subscription_service = SubscriptionService(bot)
    is_subscribed, not_subscribed = await check_gate(session, subscription_service, user)
    if not is_subscribed:
        user.is_subscribed = False
        await session.commit()
        await message.answer(
            "Avval barcha majburiy kanallarga obuna bo'ling va \"✅ Obunani tekshirish\" tugmasini bosing:",
            reply_markup=subscription_gate_keyboard(not_subscribed),
        )
        return None
    return user


async def _send_invite_content(target: Message, session: AsyncSession, user: User, bot_username: str) -> None:
    settings = await SettingsRepo(session).get()
    link = build_referral_link(bot_username, user.tg_id)
    template = settings.referral_text or "Yopiq kanalga qo'shilish uchun botga kiring: {referral_link}"
    text = template.replace("{referral_link}", link)

    user.has_generated_link = True
    await session.commit()

    if settings.referral_image_file_id:
        await target.answer_photo(settings.referral_image_file_id, caption=text)
    else:
        await target.answer(text)


@router.message(F.text == BTN_INVITE)
async def on_invite(message: Message, session: AsyncSession, bot: Bot, bot_username: str) -> None:
    user = await require_ready_user(message, session, bot)
    if user is None:
        return
    await _send_invite_content(message, session, user, bot_username)


@router.callback_query(lambda c: c.data == CB_SHOW_INVITE)
async def on_invite_inline(callback: CallbackQuery, session: AsyncSession, bot: Bot, bot_username: str) -> None:
    user = await UserRepo(session).get_by_tg_id(callback.from_user.id)
    if user is None or user.is_blocked:
        await callback.answer("Avval /start buyrug'ini yuboring.", show_alert=True)
        return
    await _send_invite_content(callback.message, session, user, bot_username)
    await callback.answer()


def _build_my_referrals_text(user: User, progress: dict) -> str:
    if user.joined_private_channel:
        secret_status = "siz kanaldasiz ✅"
    elif user.secret_link_taken:
        secret_status = "havola berilgan ⏳"
    else:
        secret_status = "olinmagan ❌"

    return (
        "📊 Sizning natijangiz:\n\n"
        f"Kerakli takliflar: {progress['required']} ta\n"
        f"✅ Tasdiqlangan: {progress['approved']} ta\n"
        f"⏳ Shartni bajarmagan: {progress['pending']} ta\n"
        f"📝 Qolgan: {progress['remaining']} ta\n\n"
        f"🔐 Maxfiy havola: {secret_status}"
    )


async def _render_my_referrals(
    session: AsyncSession, bot: Bot, user: User, settings: BotSettings, referral_service: ReferralService
) -> tuple[str, Optional[str]]:
    """Statistika matnini va (agar shu payt shartlar bajarilgan bo'lsa) avtomatik
    berilgan maxfiy havola matnini qaytaradi."""
    secret_link_text = await try_auto_grant_secret_link(session, bot, user, settings, referral_service)
    progress = await referral_service.get_progress(user.id, settings.required_referral_count)
    return _build_my_referrals_text(user, progress), secret_link_text


@router.message(F.text == BTN_MY_REFERRALS)
async def on_my_referrals(message: Message, session: AsyncSession, bot: Bot) -> None:
    user = await require_ready_user(message, session, bot)
    if user is None:
        return

    settings = await SettingsRepo(session).get()
    referral_service = ReferralService(session, SubscriptionService(bot))
    text, secret_link_text = await _render_my_referrals(session, bot, user, settings, referral_service)

    await message.answer(text, reply_markup=my_referrals_refresh_keyboard())
    if secret_link_text:
        await message.answer(secret_link_text)


@router.callback_query(lambda c: c.data == CB_REFRESH_MY_REFERRALS)
async def on_refresh_my_referrals(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    user = await UserRepo(session).get_by_tg_id(callback.from_user.id)
    if user is None:
        await callback.answer("Avval /start buyrug'ini yuboring.", show_alert=True)
        return

    settings = await SettingsRepo(session).get()
    referral_service = ReferralService(session, SubscriptionService(bot))
    text, secret_link_text = await _render_my_referrals(session, bot, user, settings, referral_service)

    try:
        await callback.message.edit_text(text, reply_markup=my_referrals_refresh_keyboard())
        await callback.answer("Yangilandi")
    except TelegramBadRequest:
        await callback.answer("O'zgarish yo'q")

    if secret_link_text:
        await callback.message.answer(secret_link_text)
