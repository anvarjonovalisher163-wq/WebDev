from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user._common import check_gate, finalize_subscription
from bot.keyboards.user import CB_CHECK_SUBSCRIPTION, main_menu_keyboard, subscription_gate_keyboard
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.subscription_service import SubscriptionService

router = Router(name="user_subscription")


@router.callback_query(lambda c: c.data == CB_CHECK_SUBSCRIPTION)
async def on_check_subscription(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
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
    await callback.message.edit_text("Asosiy menyu:", reply_markup=main_menu_keyboard())
