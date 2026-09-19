from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user._common import check_gate, finalize_subscription, get_welcome_text
from bot.keyboards.user import CB_CHECK_SUBSCRIPTION, subscription_gate_keyboard, welcome_actions_keyboard
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.subscription_service import SubscriptionService
from bot.services.user_service import build_referral_link

router = Router(name="user_subscription")


@router.callback_query(lambda c: c.data == CB_CHECK_SUBSCRIPTION)
async def on_check_subscription(
    callback: CallbackQuery, session: AsyncSession, bot: Bot, bot_username: str
) -> None:
    user = await UserRepo(session).get_by_tg_id(callback.from_user.id)
    if user is None or user.is_blocked:
        await callback.answer("Avval /start buyrug'ini yuboring.", show_alert=True)
        return

    subscription_service = SubscriptionService(bot)
    is_subscribed, not_subscribed = await check_gate(session, subscription_service, user)

    if not is_subscribed:
        await callback.answer(
            "Siz hali barcha kanallarga obuna bo'lmagansiz.", show_alert=True
        )
        await callback.message.edit_reply_markup(reply_markup=subscription_gate_keyboard(not_subscribed))
        return

    referral_service = ReferralService(session, subscription_service)
    await finalize_subscription(session, bot, user, referral_service)
    await session.commit()

    await callback.answer("Barcha kanallarga obuna tasdiqlandi!")
    await callback.message.edit_reply_markup(reply_markup=None)

    settings = await SettingsRepo(session).get()
    link = build_referral_link(bot_username, user.tg_id)
    welcome_text = get_welcome_text(settings, user.first_name, link)
    keyboard = welcome_actions_keyboard(link)

    if settings.welcome_media_file_id and settings.welcome_media_type == "photo":
        await callback.message.answer_photo(settings.welcome_media_file_id, caption=welcome_text, reply_markup=keyboard)
    elif settings.welcome_media_file_id and settings.welcome_media_type == "video":
        await callback.message.answer_video(settings.welcome_media_file_id, caption=welcome_text, reply_markup=keyboard)
    else:
        await callback.message.answer(welcome_text, reply_markup=keyboard)
