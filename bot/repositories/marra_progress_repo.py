from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.marra_campaign import MarraDailyProgress


class MarraProgressRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, participant_id: int, day_number: int) -> Optional[MarraDailyProgress]:
        result = await self.session.execute(
            select(MarraDailyProgress).where(
                MarraDailyProgress.participant_id == participant_id,
                MarraDailyProgress.day_number == day_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, participant_id: int, day_number: int) -> MarraDailyProgress:
        progress = await self.get(participant_id, day_number)
        if progress is not None:
            return progress
        progress = MarraDailyProgress(participant_id=participant_id, day_number=day_number)
        self.session.add(progress)
        await self.session.flush()
        return progress

    async def list_by_participant(self, participant_id: int) -> list[MarraDailyProgress]:
        result = await self.session.execute(
            select(MarraDailyProgress)
            .where(MarraDailyProgress.participant_id == participant_id)
            .order_by(MarraDailyProgress.day_number)
        )
        return list(result.scalars().all())

    async def add_seconds(
        self, progress: MarraDailyProgress, seconds: int, required_minutes: int
    ) -> None:
        progress.seconds_read = min(progress.seconds_read + seconds, required_minutes * 60)
        if not progress.completed and progress.seconds_read >= required_minutes * 60:
            progress.completed = True
            progress.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
