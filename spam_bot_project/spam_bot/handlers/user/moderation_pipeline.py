from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.repositories.spam_log_repo import SpamLogRepo
from spam_bot.services.crypto_service import CryptoService
from spam_bot.services.moderation_actions import ban_user
from spam_bot.services.moderation_service import MessageModerationService
from spam_bot.services.notify import notify_operators
from spam_bot.services.profile_scan_service import scan_user_profile
from spam_bot.utils.copy import ACTION_LABELS, OPERATOR_NOTICE_TEMPLATE, REASON_LABELS, SPAM_DETECTED_TEMPLATE

router = Router(name="moderation_pipeline")

_crypto: CryptoService | None = None


def init_moderation(crypto: CryptoService) -> None:
    global _crypto
    _crypto = crypto


def _service() -> MessageModerationService:
    assert _crypto is not None, "init_moderation() chaqirilmagan"
    return MessageModerationService(_crypto)


@router.message(F.chat.type.in_({"group", "supergroup"}), F.new_chat_members)
async def on_new_members(message: Message, bot: Bot, session: AsyncSession) -> None:
    group = await GroupRepo(session).get_by_chat_id(message.chat.id)
    if group is None or not group.enabled:
        return
    if group.access_until is not None and group.access_until < datetime.now(timezone.utc):
        return
    for member in message.new_chat_members or []:
        if member.is_bot:
            continue
        reason = await scan_user_profile(bot, member.id)
        if reason is None:
            continue
        await ban_user(bot, message.chat.id, member.id)
        await SpamLogRepo(session).add(message.chat.id, member.id, None, reason=reason, action="ban")
        await session.commit()
        reason_label = REASON_LABELS.get(reason, reason)
        text = SPAM_DETECTED_TEMPLATE.format(
            mention=member.mention_html(),
            reason=reason_label,
            action=ACTION_LABELS["ban"],
        )
        await bot.send_message(message.chat.id, text)
        operator_text = OPERATOR_NOTICE_TEMPLATE.format(
            group=message.chat.title or str(message.chat.id),
            mention=member.mention_html(),
            reason=reason_label,
            action=ACTION_LABELS["ban"],
        )
        await notify_operators(bot, operator_text)


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text | F.caption)
async def on_group_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    if message.text and message.text.startswith("/"):
        return
    await _service().handle_message(message, bot, session)
