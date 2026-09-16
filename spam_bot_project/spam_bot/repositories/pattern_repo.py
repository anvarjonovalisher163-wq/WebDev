from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.models.pattern import SpamPattern


class PatternRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_group(self, group_id: int) -> list[str]:
        result = await self.session.execute(
            select(SpamPattern.pattern).where(SpamPattern.group_id == group_id)
        )
        return list(result.scalars().all())

    async def add(self, group_id: int, pattern: str, added_by: int) -> SpamPattern:
        row = SpamPattern(group_id=group_id, pattern=pattern, added_by=added_by)
        self.session.add(row)
        await self.session.flush()
        return row
