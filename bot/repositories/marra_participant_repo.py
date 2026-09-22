from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.marra_campaign import MarraParticipant


class MarraParticipantRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, campaign_id: int, user_id: int) -> Optional[MarraParticipant]:
        result = await self.session.execute(
            select(MarraParticipant).where(
                MarraParticipant.campaign_id == campaign_id,
                MarraParticipant.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, participant_id: int) -> Optional[MarraParticipant]:
        return await self.session.get(MarraParticipant, participant_id)

    async def join(self, campaign_id: int, user_id: int) -> MarraParticipant:
        participant = MarraParticipant(campaign_id=campaign_id, user_id=user_id)
        self.session.add(participant)
        await self.session.flush()
        return participant

    async def list_by_campaign(self, campaign_id: int) -> list[MarraParticipant]:
        result = await self.session.execute(
            select(MarraParticipant)
            .where(MarraParticipant.campaign_id == campaign_id)
            .order_by(MarraParticipant.joined_at)
        )
        return list(result.scalars().all())

    async def list_active_by_campaign(self, campaign_id: int) -> list[MarraParticipant]:
        result = await self.session.execute(
            select(MarraParticipant).where(
                MarraParticipant.campaign_id == campaign_id,
                MarraParticipant.is_eliminated.is_(False),
            )
        )
        return list(result.scalars().all())

    async def count_by_campaign(self, campaign_id: int, eliminated: Optional[bool] = None) -> int:
        query = select(func.count()).select_from(MarraParticipant).where(
            MarraParticipant.campaign_id == campaign_id
        )
        if eliminated is not None:
            query = query.where(MarraParticipant.is_eliminated.is_(eliminated))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def eliminate(self, participant: MarraParticipant, on_day: int) -> None:
        participant.is_eliminated = True
        participant.eliminated_on_day = on_day
        await self.session.flush()
