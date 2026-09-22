from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.season import Season
from bot.models.settings import BotSettings
from bot.models.user import User
from bot.repositories.channel_repo import ChannelRepo
from bot.repositories.invite_repo import InviteRepo
from bot.services.invite_service import InviteService
from bot.services.referral_service import ReferralService


async def try_auto_grant_secret_link(
    session: AsyncSession,
    bot: Bot,
    user: User,
    settings: BotSettings,
    referral_service: ReferralService,
    season: Season,
) -> Optional[str]:
    """Foydalanuvchi barcha shartlarni bajargan, hali maxfiy havola olmagan
    va yopiq kanalga qo'shilmagan bo'lsa, avtomatik ravishda bir martalik
    taklif havolasini yaratadi va foydalanuvchiga yuborish uchun matnni
    qaytaradi. Aks holda None qaytaradi. Har bir mavsumning o'z yopiq kanali
    bo'lishi mumkin - admin uni mavsum boshida sozlashi kerak."""
    if season.secret_channel_id is None:
        return None
    if user.joined_private_channel:
        return None
    if user.secret_link_taken:
        # `secret_link_taken` - "hech bo'lmasa bir marta havola berilgan"
        # degani, "hozir ham amal qiladigan havolasi bor" degani emas.
        # Agar oldingi havola (foydalanuvchi bosmasdan) muddati o'tib
        # bekor bo'lgan bo'lsa, shu yerda abadiy to'xtab qolmasligi uchun
        # hozirgi ACTIVE havola bor-yo'qligini tekshiramiz - yo'q bo'lsa
        # yangisini beramiz.
        existing_active = await InviteRepo(session).get_active_for_user(user.id)
        if existing_active is not None:
            return None

    channels = await ChannelRepo(session).list_active()
    await referral_service.recheck_approved_before_secret_link(user.id, channels)
    progress = await referral_service.get_progress(user.id, settings.required_referral_count, season.id)
    if progress["remaining"] > 0:
        return None

    invite_service = InviteService(session, bot)
    try:
        link = await invite_service.create_one_time_link(user, settings, season)
    except TelegramAPIError as exc:
        logger.error(
            "Maxfiy havola yaratib bo'lmadi (user_id={}, tg_id={}, kanal={}): {}",
            user.id, user.tg_id, season.secret_channel_id, exc,
        )
        return (
            "🎉 Siz barcha shartlarni bajardingiz!\n\n"
            "⚠️ Ammo maxfiy havolani yaratishda texnik xatolik yuz berdi "
            "(bot kanalda administrator emas yoki huquqlari yetarli emas bo'lishi mumkin). "
            "Iltimos, admin bilan bog'laning - muammo hal bo'lgach, shu tugmani qayta bosing."
        )
    await session.commit()

    return (
        "🎉 Tabriklaymiz! Siz barcha shartlarni bajardingiz.\n\n"
        "Quyidagi havola orqali yopiq kanalga qo'shilishingiz mumkin.\n"
        f"Havola {settings.link_ttl_minutes} daqiqa davomida amal qiladi va faqat bir marta ishlatiladi.\n\n"
        f"{link.telegram_link}"
    )
