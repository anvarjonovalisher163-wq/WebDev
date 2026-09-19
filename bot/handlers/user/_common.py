from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.settings import BotSettings
from bot.models.user import User
from bot.repositories.channel_repo import ChannelRepo
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.secret_link_flow import try_auto_grant_secret_link
from bot.services.subscription_service import SubscriptionService

DEFAULT_WELCOME = "Assalomu alaykum! Botga xush kelibsiz."
DEFAULT_GATE_TEXT = (
    "Botdan foydalanish uchun avval quyidagi kanallarga obuna bo'ling va "
    "\"✅ Obunani tekshirish\" tugmasini bosing:"
)


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
    active_season = await SeasonRepo(session).get_active()
    progress = await referral_service.get_progress(
        referrer.id, settings.required_referral_count, active_season.id
    )

    try:
        await bot.send_message(
            referrer.tg_id,
            (
                "Tabriklaymiz! Siz taklif qilgan yangi foydalanuvchi barcha shartlarni bajardi.\n\n"
                f"Tasdiqlangan takliflaringiz: {progress['approved']}/{progress['required']}."
            ),
        )
        if progress["remaining"] == 0:
            secret_link_text = await try_auto_grant_secret_link(
                session, bot, referrer, settings, referral_service, active_season
            )
            if secret_link_text:
                await bot.send_message(referrer.tg_id, secret_link_text)
    except TelegramForbiddenError:
        referrer.is_blocked = True
    except TelegramBadRequest:
        pass


def get_welcome_text(settings: BotSettings, first_name: str, referral_link: str) -> str:
    text = settings.welcome_text or DEFAULT_WELCOME
    return text.replace("{ism}", first_name).replace("{referral_link}", referral_link)


def get_gate_text(settings: BotSettings) -> str:
    return settings.subscription_gate_text or DEFAULT_GATE_TEXT
