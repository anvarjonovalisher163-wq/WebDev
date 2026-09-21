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
    season_repo = SeasonRepo(session)
    active_season = await season_repo.get_active()

    # Ko'rsatiladigan hisoblagich HAQIQIY holatni aks ettirishi uchun, matnni
    # tuzishdan OLDIN barcha oldingi tasdiqlangan takliflarning majburiy
    # kanallarga obunasi qayta tekshiriladi (kimdir chiqib ketgan bo'lsa,
    # hisobdan chiqariladi). Aks holda foydalanuvchiga "5/5" deb ko'rsatilib,
    # keyin (try_auto_grant_secret_link ichida xuddi shu tekshiruv ishlagach)
    # maxfiy havola sira berilmay qolar edi - foydalanuvchi buni tushunmay qolardi.
    before_recheck = await referral_service.get_progress(
        referrer.id, settings.required_referral_count, active_season.id
    )
    await referral_service.recheck_approved_before_secret_link(referrer.id, channels)
    progress = await referral_service.get_progress(
        referrer.id, settings.required_referral_count, active_season.id
    )
    left_channels_notice = ""
    dropped = before_recheck["approved"] - progress["approved"]
    if dropped > 0:
        left_channels_notice = (
            f"\n\n⚠️ Diqqat: siz taklif qilgan {dropped} ta foydalanuvchi keyinchalik "
            "majburiy kanal(lar)dan chiqib ketgani uchun endi hisoblanmaydi."
        )

    # Taklif qilingan foydalanuvchi botga JORIY mavsum boshlanishidan OLDIN
    # ro'yxatdan o'tgan bo'lishi mumkin (masalan, havolani olib, obunani
    # kechroq tasdiqlagan). Bunday holda bu taklif joriy mavsum hisobiga
    # qo'shilmaydi - buni "0/N" ko'rsatish o'rniga aniq tushuntiramiz.
    if referral.season_id != active_season.id:
        referral_season = await season_repo.get_by_id(referral.season_id)
        old_season_name = referral_season.name if referral_season else "oldingi mavsum"
        confirmation_text = (
            "Tabriklaymiz! Siz taklif qilgan foydalanuvchi barcha shartlarni bajardi.\n\n"
            f"Diqqat: bu foydalanuvchi botdan {old_season_name} davomida (joriy mavsum "
            "boshlanishidan oldin) ro'yxatdan o'tgan edi, shuning uchun bu taklif joriy "
            "mavsum hisoblagichiga qo'shilmaydi.\n\n"
            f"Joriy mavsumdagi tasdiqlangan takliflaringiz: {progress['approved']}/{progress['required']}."
            f"{left_channels_notice}"
        )
    else:
        confirmation_text = (
            "Tabriklaymiz! Siz taklif qilgan yangi foydalanuvchi barcha shartlarni bajardi.\n\n"
            f"Tasdiqlangan takliflaringiz: {progress['approved']}/{progress['required']}."
            f"{left_channels_notice}"
        )

    try:
        await bot.send_message(referrer.tg_id, confirmation_text)
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
