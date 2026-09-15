from typing import Optional

from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user._common import check_gate
from bot.keyboards.user import CB_MENU_INVITE, CB_MENU_MY_REFERRALS, subscription_gate_keyboard
from bot.models.user import User
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.subscription_service import SubscriptionService
from bot.services.user_service import build_referral_link

router = Router(name="user_menu")


async def require_ready_user(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
) -> Optional[User]:
    user = await UserRepo(session).get_by_tg_id(callback.from_user.id)
    if user is None or user.is_blocked:
        await callback.answer("Avval /start buyrug'ini yuboring.", show_alert=True)
        return None

    subscription_service = SubscriptionService(bot)
    is_subscribed, not_subscribed = await check_gate(session, subscription_service, user)
    if not is_subscribed:
        user.is_subscribed = False
        await session.commit()
        await callback.answer("Avval barcha majburiy kanallarga obuna bo'ling.", show_alert=True)
        await callback.message.answer(
            "Quyidagi kanallarga obuna bo'ling va \"Obunani tekshirish\" tugmasini bosing:",
            reply_markup=subscription_gate_keyboard(not_subscribed),
        )
        return None
    return user


@router.callback_query(lambda c: c.data == CB_MENU_INVITE)
async def on_invite(callback: CallbackQuery, session: AsyncSession, bot: Bot, bot_username: str) -> None:
    user = await require_ready_user(callback, session, bot)
    if user is None:
        return

    settings = await SettingsRepo(session).get()
    link = build_referral_link(bot_username, user.tg_id)
    template = settings.referral_text or "Yopiq kanalga qo'shilish uchun botga kiring: {referral_link}"
    text = template.replace("{referral_link}", link)

    user.has_generated_link = True
    await session.commit()

    if settings.referral_image_file_id:
        await callback.message.answer_photo(settings.referral_image_file_id, caption=text)
    else:
        await callback.message.answer(text)
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_MENU_MY_REFERRALS)
async def on_my_referrals(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    user = await require_ready_user(callback, session, bot)
    if user is None:
        return

    settings = await SettingsRepo(session).get()
    subscription_service = SubscriptionService(bot)
    referral_service = ReferralService(session, subscription_service)
    progress = await referral_service.get_progress(user.id, settings.required_referral_count)

    secret_status = "olingan" if user.secret_link_taken else "olinmagan"
    text = (
        "Sizning natijangiz:\n\n"
        f"Kerakli takliflar: {progress['required']} ta\n"
        f"Tasdiqlangan takliflar: {progress['approved']} ta\n"
        f"Shartlarni hali bajarmaganlar: {progress['pending']} ta\n"
        f"Qolgan takliflar: {progress['remaining']} ta\n\n"
        f"Maxfiy havola: {secret_status}"
    )
    await callback.message.answer(text)
    await callback.answer()
