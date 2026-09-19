from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_SEASON_END_CONFIRM,
    CB_ADMIN_SEASON_END_PROMPT,
    CB_ADMIN_SEASONS,
    admin_main_menu_keyboard,
    season_end_confirm_keyboard,
    seasons_menu_keyboard,
)
from bot.repositories.season_repo import SeasonRepo
from bot.services.audit import log_admin_action
from bot.services.broadcast_service import BroadcastService
from bot.services.season_service import CELEBRATION_EMOJI, SeasonService

router = Router(name="admin_seasons")


@router.callback_query(lambda c: c.data == CB_ADMIN_SEASONS)
async def on_seasons_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    season_service = SeasonService(session)
    active = await SeasonRepo(session).get_active()
    leaderboard = await season_service.get_leaderboard_text(active)

    await callback.message.edit_text(
        f"Joriy mavsum: <b>{active.name}</b>\n\n{leaderboard}",
        reply_markup=seasons_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_SEASON_END_PROMPT)
async def on_season_end_prompt(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Joriy mavsum yakunlanadi, g'olib avtomatik aniqlanadi va barcha "
        "foydalanuvchilarga e'lon qilinadi, so'ng yangi mavsum 0 dan boshlanadi.\n\n"
        "Bu amalni ortga qaytarib bo'lmaydi. Davom etamizmi?",
        reply_markup=season_end_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_SEASON_END_CONFIRM)
async def on_season_end_confirm(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await callback.answer("Yakunlanmoqda...")
    await callback.message.edit_reply_markup(reply_markup=None)

    season_service = SeasonService(session)
    result = await season_service.end_current_and_start_new()

    await log_admin_action(
        session,
        callback.from_user.id,
        "end_season",
        f"season={result.closed_season.name} winner_id={result.winner.id if result.winner else None} "
        f"winner_count={result.winner_count}",
    )
    await session.commit()

    if result.winner is not None:
        try:
            await bot.send_message(
                result.winner.tg_id,
                (
                    "🏆 Tabriklaymiz! Siz <b>{season}</b> davomida eng ko'p taklif qilgan "
                    "\"Eng Faol Targibotchi\" bo'ldingiz — {count} ta tasdiqlangan taklif bilan!\n\n"
                    "Sizga alohida sovg'a beriladi, tez orada administrator siz bilan bog'lanadi."
                ).format(season=result.closed_season.name, count=result.winner_count),
            )
            await bot.send_message(result.winner.tg_id, CELEBRATION_EMOJI)
        except (TelegramForbiddenError, TelegramBadRequest):
            pass

    winner_line = (
        f"🏆 Bu mavsumning \"Eng Faol Targibotchi\"si — {result.winner.first_name}, "
        f"{result.winner_count} ta tasdiqlangan taklif bilan!"
        if result.winner is not None
        else "Bu mavsumda hech kim shartlarni bajarmadi."
    )
    announcement = (
        f"📢 {result.closed_season.name} yakunlandi!\n\n"
        f"{winner_line}\n\n"
        f"🆕 {result.new_season.name} boshlandi — barchaning hisoblagichi 0 dan boshlanadi, omad tilaymiz!"
    )
    report = await BroadcastService(session, bot).send_text_to_all(announcement)

    await callback.message.answer(
        "Mavsum yakunlandi va e'lon yuborildi.\n\n"
        f"G'olib: {result.winner.first_name if result.winner else '(aniqlanmadi)'}\n"
        f"Yangi mavsum: {result.new_season.name}\n\n"
        f"E'lon yetkazildi: {report.success}/{report.total} "
        f"(bloklaganlar: {report.blocked}, xatolik: {report.failed})",
        reply_markup=admin_main_menu_keyboard(),
    )
