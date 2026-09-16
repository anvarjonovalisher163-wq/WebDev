from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.config import settings
from spam_bot.filters.is_group_admin import IsGroupAdmin
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.services.key_link_service import key_link_service
from spam_bot.utils.copy import (
    DISABLE_SUCCESS,
    ENABLE_SUCCESS,
    GROUP_LIMIT_REACHED,
    HELP_TEXT,
    PRIVACY_TEXT,
    SETKEY_CANNOT_DM,
    SETKEY_DM_ONLY,
    SETKEY_LINK_SENT_TO_DM,
    SETKEY_PROMPT,
)

router = Router(name="commands")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(PRIVACY_TEXT)


@router.message(Command("enable"), F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())
async def cmd_enable(message: Message, session: AsyncSession) -> None:
    repo = GroupRepo(session)
    group = await repo.get_or_create(message.chat.id, message.chat.title, message.from_user.id)
    if not group.enabled:
        active_count = await repo.count_enabled_for_owner(message.from_user.id)
        if active_count >= settings.max_groups_per_owner:
            await message.answer(GROUP_LIMIT_REACHED)
            return
        await repo.set_enabled(group, True)
        await session.commit()
    await message.answer(ENABLE_SUCCESS)


@router.message(Command("disable"), F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())
async def cmd_disable(message: Message, session: AsyncSession) -> None:
    repo = GroupRepo(session)
    group = await repo.get_by_chat_id(message.chat.id)
    if group is not None and group.enabled:
        await repo.set_enabled(group, False)
        await session.commit()
    await message.answer(DISABLE_SUCCESS)


@router.message(Command("setkey"))
async def cmd_setkey(message: Message, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(SETKEY_DM_ONLY)
        return
    if not await IsGroupAdmin()(message, bot):
        return

    token = key_link_service.create_token(message.chat.id, message.from_user.id)
    link = f"{settings.base_url.rstrip('/')}/setkey/{token}"
    try:
        await bot.send_message(message.from_user.id, SETKEY_PROMPT.format(link=link))
    except TelegramForbiddenError:
        await message.answer(SETKEY_CANNOT_DM)
        return
    await message.answer(SETKEY_LINK_SENT_TO_DM)
