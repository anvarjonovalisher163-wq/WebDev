from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User
from bot.repositories.admin_repo import AdminRepo


def certificate_review_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin:cert_approve:{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin:cert_reject:{user_id}"),
            ]
        ]
    )


async def submit_certificate_name_for_approval(
    session: AsyncSession, bot: Bot, user: User, full_name: str
) -> None:
    """Foydalanuvchi sertifikat uchun ism-familiyasini yuborgach chaqiriladi:
    uni saqlaydi va BARCHA adminlarga tasdiqlash/rad etish tugmalari bilan
    yuboradi. Sertifikat faqat admin ✅ Tasdiqlash bosgandan keyingina
    generatsiya qilinib yuboriladi - shu bilan noto'g'ri/hazil ism kiritish
    holatlaridan himoyalanadi."""
    user.cert_full_name = full_name
    user.cert_requested_at = datetime.now(timezone.utc)
    await session.commit()

    username_part = f" (@{user.username})" if user.username else ""
    notice = (
        "🆕 Yangi sertifikat so'rovi:\n\n"
        f"Ism-familiya: {full_name}\n"
        f"Foydalanuvchi: {user.first_name}{username_part} [ID: {user.tg_id}]"
    )

    admins = await AdminRepo(session).list_all()
    for admin in admins:
        try:
            await bot.send_message(admin.tg_id, notice, reply_markup=certificate_review_keyboard(user.id))
        except (TelegramForbiddenError, TelegramBadRequest):
            continue
