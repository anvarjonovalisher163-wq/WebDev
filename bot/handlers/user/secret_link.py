from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.menu import require_ready_user
from bot.keyboards.user import CB_MENU_SECRET_LINK
from bot.repositories.channel_repo import ChannelRepo
from bot.repositories.invite_repo import InviteRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.services.invite_service import InviteService
from bot.services.referral_service import ReferralService
from bot.services.subscription_service import SubscriptionService

router = Router(name="user_secret_link")


@router.callback_query(lambda c: c.data == CB_MENU_SECRET_LINK)
async def on_secret_link(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    user = await require_ready_user(callback, session, bot)
    if user is None:
        return

    settings = await SettingsRepo(session).get()
    if settings.secret_channel_id is None:
        await callback.answer("Hozircha maxfiy kanal sozlanmagan.", show_alert=True)
        return

    if user.joined_private_channel:
        await callback.message.answer("Siz allaqachon yopiq kanalga qo'shilgansiz.")
        await callback.answer()
        return

    invite_repo = InviteRepo(session)
    now = datetime.now(timezone.utc)

    existing_active = await invite_repo.get_active_for_user(user.id)
    if existing_active is not None and existing_active.expires_at > now:
        remaining_minutes = max(int((existing_active.expires_at - now).total_seconds() // 60), 1)
        await callback.message.answer(
            "Sizda faol taklif havolasi mavjud:\n\n"
            f"{existing_active.telegram_link}\n\n"
            f"Havola yana {remaining_minutes} daqiqa davomida amal qiladi va faqat bir marta ishlatiladi."
        )
        await callback.answer()
        return

    subscription_service = SubscriptionService(bot)
    referral_service = ReferralService(session, subscription_service)
    channels = await ChannelRepo(session).list_active()

    await referral_service.recheck_approved_before_secret_link(user.id, channels)
    progress = await referral_service.get_progress(user.id, settings.required_referral_count)

    if progress["remaining"] > 0:
        await callback.message.answer(
            "Maxfiy havolani olish uchun yana "
            f"{progress['remaining']} ta tasdiqlangan foydalanuvchi taklif qilishingiz kerak."
        )
        await callback.answer()
        return

    if user.secret_link_taken:
        if not settings.reissue_allowed:
            await callback.message.answer(
                "Sizga avval berilgan havolaning muddati tugagan va qayta olish imkoni yo'q."
            )
            await callback.answer()
            return
        if user.secret_link_attempts >= settings.max_reissue_attempts:
            await callback.message.answer("Qayta havola olish limitiga yetdingiz.")
            await callback.answer()
            return

    invite_service = InviteService(session, bot)
    link = await invite_service.create_one_time_link(user, settings)
    await session.commit()

    await callback.message.answer(
        "Tabriklaymiz! Siz barcha shartlarni bajardingiz.\n\n"
        "Quyidagi havola orqali yopiq kanalga qo'shilishingiz mumkin.\n"
        f"Havola {settings.link_ttl_minutes} daqiqa davomida amal qiladi va faqat bir marta ishlatiladi.\n\n"
        f"{link.telegram_link}"
    )
    await callback.answer()
