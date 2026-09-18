from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.config import settings
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.utils.copy import ENABLE_TRIAL_STARTED, GROUP_LIMIT_REACHED

router = Router(name="chat_member_events")

_ADMIN_STATUSES = {"administrator", "creator"}


@router.my_chat_member()
async def on_bot_membership_changed(update: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    if update.chat.type not in ("group", "supergroup"):
        return

    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status
    repo = GroupRepo(session)

    if new_status in _ADMIN_STATUSES and old_status not in _ADMIN_STATUSES:
        existing = await repo.get_by_chat_id(update.chat.id)
        is_new = existing is None
        group = await repo.get_or_create(update.chat.id, update.chat.title, update.from_user.id, settings.trial_days)

        if not group.enabled:
            active_count = await repo.count_enabled_for_owner(update.from_user.id)
            if active_count >= settings.max_groups_per_owner:
                await bot.send_message(update.chat.id, GROUP_LIMIT_REACHED)
                try:
                    await bot.leave_chat(update.chat.id)
                except TelegramBadRequest:
                    pass
                return
            await repo.set_enabled(group, True)
            await session.commit()

        if is_new and group.access_until is not None:
            days_left = max(1, (group.access_until - datetime.now(timezone.utc)).days)
            await bot.send_message(update.chat.id, ENABLE_TRIAL_STARTED.format(days=days_left))

    elif new_status not in _ADMIN_STATUSES and old_status in _ADMIN_STATUSES:
        group = await repo.get_by_chat_id(update.chat.id)
        if group is not None and group.enabled:
            await repo.set_enabled(group, False)
            await session.commit()
