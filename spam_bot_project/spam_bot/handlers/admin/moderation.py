from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.filters.is_group_admin import IsGroupAdmin
from spam_bot.repositories.mute_repo import MuteRepo
from spam_bot.services.moderation_actions import ban_user, mute_until, mute_user
from spam_bot.utils.copy import BAN_DONE, MUTE_DONE, REPLY_REQUIRED

router = Router(name="admin_moderation")


@router.message(Command("ban"), F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())
async def cmd_ban(message: Message, bot: Bot) -> None:
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if target is None:
        await message.answer(REPLY_REQUIRED)
        return
    await ban_user(bot, message.chat.id, target.id)
    await message.answer(BAN_DONE.format(name=target.mention_html()))


@router.message(Command("mute"), F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())
async def cmd_mute(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if target is None:
        await message.answer(REPLY_REQUIRED)
        return
    until = mute_until()
    await mute_user(bot, message.chat.id, target.id, until)
    await MuteRepo(session).create(message.chat.id, target.id, reason="admin_command", muted_until=until)
    await session.commit()
    await message.answer(MUTE_DONE.format(name=target.mention_html()))
