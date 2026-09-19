from typing import Optional

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.settings import BotSettings
from bot.models.user import User
from bot.repositories.channel_repo import ChannelRepo
from bot.services.invite_service import InviteService
from bot.services.referral_service import ReferralService


async def try_auto_grant_secret_link(
    session: AsyncSession,
    bot: Bot,
    user: User,
    settings: BotSettings,
    referral_service: ReferralService,
    season_id: int,
) -> Optional[str]:
    """Foydalanuvchi barcha shartlarni bajargan, hali maxfiy havola olmagan
    va yopiq kanalga qo'shilmagan bo'lsa, avtomatik ravishda bir martalik
    taklif havolasini yaratadi va foydalanuvchiga yuborish uchun matnni
    qaytaradi. Aks holda None qaytaradi."""
    if settings.secret_channel_id is None:
        return None
    if user.joined_private_channel or user.secret_link_taken:
        return None

    channels = await ChannelRepo(session).list_active()
    await referral_service.recheck_approved_before_secret_link(user.id, channels)
    progress = await referral_service.get_progress(user.id, settings.required_referral_count, season_id)
    if progress["remaining"] > 0:
        return None

    invite_service = InviteService(session, bot)
    link = await invite_service.create_one_time_link(user, settings)
    await session.commit()

    return (
        "🎉 Tabriklaymiz! Siz barcha shartlarni bajardingiz.\n\n"
        "Quyidagi havola orqali yopiq kanalga qo'shilishingiz mumkin.\n"
        f"Havola {settings.link_ttl_minutes} daqiqa davomida amal qiladi va faqat bir marta ishlatiladi.\n\n"
        f"{link.telegram_link}"
    )
