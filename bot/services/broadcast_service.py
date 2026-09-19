import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User
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

    async def _deliver(self, user: User, send: Callable[[], Awaitable[None]]) -> str:
        try:
            await send()
            return "success"
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await send()
                return "success"
            except Exception:
                return "failed"
        except TelegramForbiddenError:
            user.is_blocked = True
            return "blocked"
        except TelegramBadRequest:
            return "failed"

    async def _run(self, make_send: Callable[[User], Callable[[], Awaitable[None]]]) -> BroadcastReport:
        users = await self.user_repo.list_not_blocked()
        counts = {"success": 0, "blocked": 0, "failed": 0}

        for user in users:
            outcome = await self._deliver(user, make_send(user))
            counts[outcome] += 1
            await asyncio.sleep(_THROTTLE_SECONDS)

        await self.session.commit()
        return BroadcastReport(total=len(users), **counts)

    async def send_to_all(self, from_chat_id: int, message_id: int) -> BroadcastReport:
        return await self._run(
            lambda user: (
                lambda: self.bot.copy_message(
                    chat_id=user.tg_id, from_chat_id=from_chat_id, message_id=message_id
                )
            )
        )

    async def send_text_to_all(self, text: str) -> BroadcastReport:
        """Tizim tomonidan avtomatik yaratilgan matnli e'lonni (masalan, mavsum
        yakuni haqida) barcha foydalanuvchilarga yuboradi."""
        return await self._run(lambda user: (lambda: self.bot.send_message(user.tg_id, text)))
