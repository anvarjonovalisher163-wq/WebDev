from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.settings import BotSettings
from bot.models.user import User
from bot.repositories.channel_repo import ChannelRepo
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.subscription_service import SubscriptionService

DEFAULT_WELCOME = "Assalomu alaykum! Botga xush kelibsiz."


async def check_gate(
    session: AsyncSession, subscription_service: SubscriptionService, user: User
) -> tuple[bool, list]:
    """True/False - barcha majburiy kanallarga obuna bo'lganmi, va obuna bo'lmagan kanallar ro'yxati."""
    channels = await ChannelRepo(session).list_active()
    if not channels:
        return True, []
    not_subscribed = await subscription_service.get_not_subscribed(user.tg_id, channels)
    return (len(not_subscribed) == 0), not_subscribed


async def finalize_subscription(
    session: AsyncSession,
    bot: Bot,
    user: User,
    referral_service: ReferralService,
) -> None:
    """Foydalanuvchi obunasi tasdiqlangach, uni taklif qilgan referrerning
    referral yozuvini tasdiqlashga urinadi va referrerga xabar yuboradi."""
    user.is_subscribed = True

    referral_repo = ReferralRepo(session)
    referral = await referral_repo.get_by_referred_id(user.id)
    if referral is None:
        return

    channels = await ChannelRepo(session).list_active()
    was_confirmed = await referral_service.try_confirm(referral, user, channels)
    if not was_confirmed:
        return

    user_repo = UserRepo(session)
    referrer = await user_repo.get_by_id(referral.referrer_id)
    if referrer is None:
        return

    settings = await SettingsRepo(session).get()
    progress = await referral_service.get_progress(referrer.id, settings.required_referral_count)

    try:
        await bot.send_message(
            referrer.tg_id,
            (
                "Tabriklaymiz! Siz taklif qilgan yangi foydalanuvchi barcha shartlarni bajardi.\n\n"
                f"Tasdiqlangan takliflaringiz: {progress['approved']}/{progress['required']}."
            ),
        )
        if progress["remaining"] == 0:
            await bot.send_message(
                referrer.tg_id,
                "Tabriklaymiz! Siz barcha shartlarni bajardingiz. Endi maxfiy havolani olishingiz mumkin.",
            )
    except TelegramBadRequest:
        pass


def get_welcome_text(settings: BotSettings) -> str:
    return settings.welcome_text or DEFAULT_WELCOME
