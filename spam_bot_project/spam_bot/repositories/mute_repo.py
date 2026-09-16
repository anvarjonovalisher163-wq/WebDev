from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.models.mute_record import MuteRecord


class MuteRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, chat_id: int, user_id: int, reason: str, muted_until: datetime) -> MuteRecord:
        row = MuteRecord(chat_id=chat_id, user_id=user_id, reason=reason, muted_until=muted_until, active=True)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_active(self, chat_id: int, user_id: int) -> MuteRecord | None:
        result = await self.session.execute(
            select(MuteRecord).where(
                MuteRecord.chat_id == chat_id,
                MuteRecord.user_id == user_id,
                MuteRecord.active.is_(True),
            )
        )
        return result.scalars().first()

    async def deactivate(self, record: MuteRecord) -> None:
        record.active = False
        await self.session.flush()

    async def list_expired(self) -> list[MuteRecord]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(MuteRecord).where(MuteRecord.active.is_(True), MuteRecord.muted_until <= now)
        )
        return list(result.scalars().all())
