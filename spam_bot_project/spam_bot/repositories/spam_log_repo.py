from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.models.spam_log import SpamLog


class SpamLogRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, chat_id: int, user_id: int, message_text: str | None, reason: str, action: str) -> SpamLog:
        row = SpamLog(
            chat_id=chat_id,
            user_id=user_id,
            message_text=(message_text or "")[:2000] or None,
            reason=reason,
            action=action,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def count_for_chat(self, chat_id: int, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(SpamLog).where(SpamLog.chat_id == chat_id, SpamLog.created_at >= since)
        )
        return result.scalar_one()

    async def count_total_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(SpamLog).where(SpamLog.created_at >= since)
        )
        return result.scalar_one()

    async def purge_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(delete(SpamLog).where(SpamLog.created_at < cutoff))
        return result.rowcount or 0
