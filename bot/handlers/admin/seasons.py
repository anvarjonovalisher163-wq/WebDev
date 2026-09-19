from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_SEASON_END_CONFIRM,
    CB_ADMIN_SEASON_END_PROMPT,
    CB_ADMIN_SEASONS,
    admin_main_menu_keyboard,
    cancel_keyboard,
    season_end_confirm_keyboard,
    seasons_menu_keyboard,
)
from bot.repositories.season_repo import SeasonRepo
from bot.services.audit import log_admin_action
from bot.services.season_service import CELEBRATION_EMOJI, SeasonService
from bot.states.admin_states import SeasonStates

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
        "Joriy mavsum yakunlanadi, g'olib avtomatik aniqlanadi (unga shaxsan "
        "xabar beriladi) va barchaning hisoblagichi 0 dan boshlanadi.\n\n"
        "Bu amalni ortga qaytarib bo'lmaydi. Davom etamizmi?",
        reply_markup=season_end_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_SEASON_END_CONFIRM)
async def on_season_end_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SeasonStates.waiting_new_name)
    await callback.message.edit_text(
        "Yangi mavsum uchun nom kiriting (masalan: \"1-mavsum\", \"2-mavsum\" yoki "
        "istalgan boshqa nom):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SeasonStates.waiting_new_name)
async def on_season_new_name_received(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("Nom bo'sh bo'lishi mumkin emas. Qayta kiriting:", reply_markup=cancel_keyboard())
        return

    await state.clear()

    season_service = SeasonService(session)
    result = await season_service.end_current_and_start_new(new_name)

    await log_admin_action(
        session,
        message.from_user.id,
        "end_season",
        f"season={result.closed_season.name} new_season={result.new_season.name} "
        f"winner_id={result.winner.id if result.winner else None} winner_count={result.winner_count}",
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
        f"G'olib: {result.winner.first_name} ({result.winner_count} ta tasdiqlangan taklif) - "
        "unga shaxsan tabrik xabari yuborildi."
        if result.winner is not None
        else "G'olib: (bu mavsumda hech kim shartlarni bajarmadi)"
    )
    await message.answer(
        f"✅ {result.closed_season.name} yakunlandi, {result.new_season.name} boshlandi.\n\n"
        f"{winner_line}\n\n"
        "⚠️ Yangi mavsum uchun yopiq kanal hali sozlanmagan - \"🔐 Maxfiy kanal "
        "sozlamalari\" bo'limidan yangi (yoki eski) kanalni qayta belgilang.",
        reply_markup=admin_main_menu_keyboard(),
    )
