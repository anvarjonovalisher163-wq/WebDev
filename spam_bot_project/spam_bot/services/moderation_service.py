import time
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.config import settings
from spam_bot.keyboards.moderation import unban_keyboard, unmute_keyboard
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.repositories.mute_repo import MuteRepo
from spam_bot.repositories.pattern_repo import PatternRepo
from spam_bot.repositories.spam_log_repo import SpamLogRepo
from spam_bot.repositories.usage_repo import UsageRepo
from spam_bot.services.ai_moderation_service import AIModerationService
from spam_bot.services.crypto_service import CryptoService
from spam_bot.services.link_scanner import find_dangerous_link
from spam_bot.services.moderation_actions import ban_user, delete_message_safe, mute_until, mute_user
from spam_bot.services.notify import notify_operators
from spam_bot.services.pattern_service import PatternService
from spam_bot.services.profile_scan_service import scan_user_profile
from spam_bot.services.raid_detector import raid_detector
from spam_bot.services.ratelimit import SlidingWindowRateLimiter
from spam_bot.utils.copy import ACTION_LABELS, ENABLE_EXPIRED_NOTICE, OPERATOR_NOTICE_TEMPLATE, REASON_LABELS

pattern_service = PatternService()
ai_moderation_service = AIModerationService(settings.gemini_model)
ai_rate_limiter = SlidingWindowRateLimiter(max_per_minute=20)

_EXPIRY_NOTICE_COOLDOWN = 24 * 3600  # bir guruhga kuniga bir marta eslatma
_expiry_notified: dict[int, float] = {}


class MessageModerationService:
    def __init__(self, crypto: CryptoService) -> None:
        self._crypto = crypto

    async def handle_message(self, message: Message, bot: Bot, session: AsyncSession) -> None:
        if message.chat.type not in ("group", "supergroup"):
            return
        if message.from_user is None or message.from_user.is_bot:
            return

        group_repo = GroupRepo(session)
        group = await group_repo.get_by_chat_id(message.chat.id)
        if group is None or not group.enabled:
            return
        if group.access_until is not None and group.access_until < datetime.now(timezone.utc):
            last_notified = _expiry_notified.get(group.chat_id)
            now_mono = time.monotonic()
            if last_notified is None or now_mono - last_notified > _EXPIRY_NOTICE_COOLDOWN:
                _expiry_notified[group.chat_id] = now_mono
                await bot.send_message(group.chat_id, ENABLE_EXPIRED_NOTICE)
            return

        profile_reason = await scan_user_profile(bot, group.chat_id, message.from_user.id)
        if profile_reason:
            await self._act(session, bot, group.chat_id, message, reason=profile_reason, action="ban")
            return

        text = message.text or message.caption or ""

        dangerous_link = find_dangerous_link(text)
        if dangerous_link:
            await self._act(session, bot, group.chat_id, message, reason="malware_link", action="ban")
            return

        group_patterns = await PatternRepo(session).list_for_group(group.id)
        matched_keyword = pattern_service.match(text, group_patterns)
        if matched_keyword:
            await self._act(session, bot, group.chat_id, message, reason="keyword", action="ban")
            return

        if text and group.gemini_key_encrypted and ai_rate_limiter.allow(group.chat_id):
            api_key = self._crypto.decrypt(group.gemini_key_encrypted)
            if api_key:
                result = await ai_moderation_service.classify(text, api_key)
                if result is not None:
                    await UsageRepo(session).add(group.chat_id, result.input_tokens, result.output_tokens)
                    await session.commit()
                    if result.is_violation:
                        await self._act(session, bot, group.chat_id, message, reason="ai", action="ban")
                        return

        if text:
            raid_users = raid_detector.register(group.chat_id, message.from_user.id, text)
            if raid_users:
                await delete_message_safe(bot, group.chat_id, message.message_id)
                for uid in raid_users:
                    await self._apply_action(session, bot, group.chat_id, uid, action="ban")
                    await SpamLogRepo(session).add(group.chat_id, uid, text, reason="raid", action="ban")
                await session.commit()
                await self._notify(
                    bot, group.chat_id, raid_users[0], "Bir nechta akkaunt", reason="raid", action="ban",
                    group_title=message.chat.title,
                )

    async def _act(self, session: AsyncSession, bot: Bot, chat_id: int, message: Message, reason: str, action: str) -> None:
        text = message.text or message.caption or ""
        user_id = message.from_user.id
        await delete_message_safe(bot, chat_id, message.message_id)
        await self._apply_action(session, bot, chat_id, user_id, action)
        await SpamLogRepo(session).add(chat_id, user_id, text, reason=reason, action=action)
        await session.commit()
        name = message.from_user.mention_html() if message.from_user else str(user_id)
        await self._notify(bot, chat_id, user_id, name, reason=reason, action=action, group_title=message.chat.title)

    async def _apply_action(self, session: AsyncSession, bot: Bot, chat_id: int, user_id: int, action: str) -> None:
        if action == "ban":
            await ban_user(bot, chat_id, user_id)
        elif action == "mute":
            until = mute_until()
            await mute_user(bot, chat_id, user_id, until)
            await MuteRepo(session).create(chat_id, user_id, reason=action, muted_until=until)

    async def _notify(self, bot: Bot, chat_id: int, user_id: int, name: str, reason: str, action: str, group_title: str | None = None) -> None:
        reason_label = REASON_LABELS.get(reason, reason)
        action_label = ACTION_LABELS.get(action, action)
        keyboard = unban_keyboard(chat_id, user_id) if action == "ban" else unmute_keyboard(chat_id, user_id) if action == "mute" else None

        operator_text = OPERATOR_NOTICE_TEMPLATE.format(
            group=group_title or str(chat_id), mention=name, reason=reason_label, action=action_label
        )
        await notify_operators(bot, operator_text, reply_markup=keyboard)
