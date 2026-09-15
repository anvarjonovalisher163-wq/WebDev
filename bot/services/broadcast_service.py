import asyncio
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepo

_THROTTLE_SECONDS = 0.05  # ~20 xabar/soniya, Telegram limitlariga rioya qilish uchun


@dataclass
class BroadcastReport:
    total: int
    success: int
    blocked: int
    failed: int


class BroadcastService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.user_repo = UserRepo(session)

    async def send_to_all(self, from_chat_id: int, message_id: int) -> BroadcastReport:
        users = await self.user_repo.list_not_blocked()
        success = blocked = failed = 0

        for user in users:
            try:
                await self.bot.copy_message(
                    chat_id=user.tg_id, from_chat_id=from_chat_id, message_id=message_id
                )
                success += 1
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    await self.bot.copy_message(
                        chat_id=user.tg_id, from_chat_id=from_chat_id, message_id=message_id
                    )
                    success += 1
                except Exception:
                    failed += 1
            except TelegramForbiddenError:
                user.is_blocked = True
                blocked += 1
            except TelegramBadRequest:
                failed += 1

            await asyncio.sleep(_THROTTLE_SECONDS)

        await self.session.commit()
        return BroadcastReport(total=len(users), success=success, blocked=blocked, failed=failed)
