from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.models.usage_log import UsageLog


class UsageRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, chat_id: int, input_tokens: int, output_tokens: int) -> UsageLog:
        row = UsageLog(chat_id=chat_id, input_tokens=input_tokens, output_tokens=output_tokens)
        self.session.add(row)
        await self.session.flush()
        return row

    async def totals_since(self, chat_id: int, since: datetime) -> tuple[int, int]:
        result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.input_tokens), 0), func.coalesce(func.sum(UsageLog.output_tokens), 0))
            .where(UsageLog.chat_id == chat_id, UsageLog.created_at >= since)
        )
        row = result.one()
        return int(row[0]), int(row[1])

    async def purge_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(delete(UsageLog).where(UsageLog.created_at < cutoff))
        return result.rowcount or 0
