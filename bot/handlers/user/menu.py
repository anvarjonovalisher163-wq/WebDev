from typing import Optional

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user._common import check_gate
from bot.keyboards.user import (
    CB_REFRESH_MY_REFERRALS,
    CB_SHOW_INVITE,
    CB_SHOW_MY_REFERRALS,
    CB_SHOW_SHARE,
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

# Eski (endi ishlatilmaydigan) pastki klaviaturadagi tugma matnlari - faqat
# foydalanuvchi ekranida hali qolib ketgan bo'lishi mumkin bo'lgan eski
# klaviaturani tozalash uchun saqlanadi.
_LEGACY_BTN_INVITE = "🔗 Taklif qilish"
_LEGACY_BTN_MY_REFERRALS = "📊 Mening takliflarim"


async def _resolve_active_user(
    session: AsyncSession, bot: Bot, tg_id: int
) -> tuple[Optional[User], list]:
    """(None, []) - topilmadi/bloklangan; (None, not_subscribed) - obuna yo'q; (user, []) - tayyor."""
    user = await UserRepo(session).get_by_tg_id(tg_id)
    if user is None or user.is_blocked:
        return None, []

    subscription_service = SubscriptionService(bot)
    is_subscribed, not_subscribed = await check_gate(session, subscription_service, user)
    if not is_subscribed:
        user.is_subscribed = False
        await session.commit()
        return None, not_subscribed
    return user, []


async def _require_ready_user_cb(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> Optional[User]:
    user, not_subscribed = await _resolve_active_user(session, bot, callback.from_user.id)
    if user is not None:
        return user

    if not_subscribed:
        await callback.answer("Avval barcha majburiy kanallarga obuna bo'ling.", show_alert=True)
        await callback.message.answer(
            "Quyidagi kanallarga obuna bo'ling va \"✅ Obunani tekshirish\" tugmasini bosing:",
            reply_markup=subscription_gate_keyboard(not_subscribed),
        )
    else:
        await callback.answer("Avval /start buyrug'ini yuboring.", show_alert=True)
    return None


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


@router.callback_query(lambda c: c.data == CB_SHOW_INVITE)
async def on_invite_inline(callback: CallbackQuery, session: AsyncSession, bot: Bot, bot_username: str) -> None:
    user = await _require_ready_user_cb(callback, session, bot)
    if user is None:
        return
    await _send_invite_content(callback.message, session, user, bot_username)
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_SHOW_SHARE)
async def on_share_inline(callback: CallbackQuery, session: AsyncSession, bot: Bot, bot_username: str) -> None:
    user = await _require_ready_user_cb(callback, session, bot)
    if user is None:
        return
    await _send_invite_content(callback.message, session, user, bot_username)
    await callback.answer("Yuqoridagi postni forward tugmasi orqali do'stingizga yuboring 👆")


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


@router.callback_query(lambda c: c.data == CB_SHOW_MY_REFERRALS)
async def on_my_referrals_inline(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    user = await _require_ready_user_cb(callback, session, bot)
    if user is None:
        return

    settings = await SettingsRepo(session).get()
    referral_service = ReferralService(session, SubscriptionService(bot))
    text, secret_link_text = await _render_my_referrals(session, bot, user, settings, referral_service)

    await callback.message.answer(text, reply_markup=my_referrals_refresh_keyboard())
    await callback.answer()
    if secret_link_text:
        await callback.message.answer(secret_link_text)


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


@router.message(F.text.in_({_LEGACY_BTN_INVITE, _LEGACY_BTN_MY_REFERRALS}))
async def on_legacy_menu_button(message: Message) -> None:
    """Eski pastki klaviatura hali ba'zi foydalanuvchilar ekranida qolgan
    bo'lishi mumkin - uni bosganda klaviaturani tozalab, yangi xabar
    tuzilishiga yo'naltiramiz."""
    await message.answer(
        "Yangilanish: bu tugmalar endi xabar ostida (inline) ko'rinadi. /start ni qayta bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
