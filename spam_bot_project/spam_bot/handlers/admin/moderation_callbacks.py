from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.repositories.mute_repo import MuteRepo
from spam_bot.services.moderation_actions import unban_user, unmute_user
from spam_bot.utils.copy import UNBAN_DONE, UNMUTE_DONE

router = Router(name="admin_moderation_callbacks")

_ADMIN_STATUSES = {"administrator", "creator"}


async def _is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except TelegramBadRequest:
        return False
    return member.status in _ADMIN_STATUSES


@router.callback_query(F.data.startswith("unban:"))
async def on_unban(callback: CallbackQuery, bot: Bot) -> None:
    _, chat_id_s, user_id_s = callback.data.split(":")
    chat_id, user_id = int(chat_id_s), int(user_id_s)
    if not await _is_admin(bot, chat_id, callback.from_user.id):
        await callback.answer()
        return
    await unban_user(bot, chat_id, user_id)
    await callback.message.edit_text(f"{callback.message.text}\n\n{UNBAN_DONE}", reply_markup=None)
    await callback.answer(UNBAN_DONE)


@router.callback_query(F.data.startswith("unmute:"))
async def on_unmute(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    _, chat_id_s, user_id_s = callback.data.split(":")
    chat_id, user_id = int(chat_id_s), int(user_id_s)
    if not await _is_admin(bot, chat_id, callback.from_user.id):
        await callback.answer()
        return
    await unmute_user(bot, chat_id, user_id)
    record = await MuteRepo(session).get_active(chat_id, user_id)
    if record is not None:
        await MuteRepo(session).deactivate(record)
        await session.commit()
    await callback.message.edit_text(f"{callback.message.text}\n\n{UNMUTE_DONE}", reply_markup=None)
    await callback.answer(UNMUTE_DONE)
