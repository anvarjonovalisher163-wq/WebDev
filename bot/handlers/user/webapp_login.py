import hashlib
import secrets

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings as app_settings
from bot.repositories.user_repo import UserRepo
from bot.repositories.web_session_repo import LOGIN_TOKEN_TTL_MINUTES, WebLoginTokenRepo

router = Router(name="user_webapp_login")


@router.message(Command("webapp"))
async def cmd_webapp_login(message: Message, session: AsyncSession) -> None:
    """Telegram'dan TASHQARIDA (oddiy brauzerda) Mini App'ga kirish uchun
    bir martalik, tez eskiruvchi havola beradi. Ochilganda brauzerga
    uzoq muddatli sessiya cookie o'rnatiladi - shu tariqa foydalanuvchi
    sahifani bosh ekranga ilova sifatida o'rnatib, Telegram'siz ham
    foydalana oladi (masalan Marra 2.0 kitob o'qish sahifasi uchun)."""
    if not app_settings.webapp_url:
        await message.answer("Web ilova hali sozlanmagan.")
        return

    user = await UserRepo(session).get_by_tg_id(message.from_user.id)
    if user is None:
        await message.answer("Avval /start bosing.")
        return

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    await WebLoginTokenRepo(session).create(user.id, token_hash)
    await session.commit()

    login_url = f"{app_settings.webapp_url}/login?t={raw_token}"
    await message.answer(
        "🌐 Quyidagi havola orqali web ilovani oddiy brauzerda oching "
        f"({LOGIN_TOKEN_TTL_MINUTES} daqiqa ichida, faqat bir marta ishlaydi):\n\n"
        f"{login_url}\n\n"
        "Ochilgandan keyin brauzeringiz \"Bosh ekranga qo'shish\" orqali "
        "ilova sifatida o'rnatib olishingiz mumkin."
    )
