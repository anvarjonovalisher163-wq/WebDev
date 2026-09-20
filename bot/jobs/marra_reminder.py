from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from loguru import logger

from bot.db.session import async_session_factory
from bot.handlers.admin.marra import DEFAULT_MARRA_REMINDER_TEXT
from bot.keyboards.user import marra_keyboard
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo

TASHKENT_TZ = ZoneInfo("Asia/Tashkent")


async def send_marra_reminders_job(bot: Bot) -> None:
    """Har soatning boshida ishga tushadi, lekin faqat joriy soat admin
    sozlagan eslatma soatiga to'g'ri kelgandagina xabar yuboradi - shunda
    admin soatni istalgan payt o'zgartirsa, scheduler'ni qayta sozlashning
    hojati bo'lmaydi."""
    now = datetime.now(TASHKENT_TZ)

    async with async_session_factory() as session:
        settings = await SettingsRepo(session).get()
        if not settings.marra_url or settings.marra_reminder_hour != now.hour:
            return
        if settings.marra_end_date and now.date() > settings.marra_end_date:
            return

        text = settings.marra_reminder_text or DEFAULT_MARRA_REMINDER_TEXT
        keyboard = marra_keyboard(settings.marra_url, is_participant=True)
        participants = await UserRepo(session).list_marra_participants()

        sent = 0
        for user in participants:
            try:
                await bot.send_message(user.tg_id, text, reply_markup=keyboard)
                sent += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                continue

        if participants:
            logger.info(f"Marra eslatmasi {sent}/{len(participants)} ishtirokchiga yuborildi")
