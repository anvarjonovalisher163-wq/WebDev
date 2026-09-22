from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.marra_campaign import MarraCampaign


class MarraCampaignRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, campaign_id: int) -> Optional[MarraCampaign]:
        return await self.session.get(MarraCampaign, campaign_id)

    async def list_all(self) -> list[MarraCampaign]:
        result = await self.session.execute(
            select(MarraCampaign).order_by(MarraCampaign.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[MarraCampaign]:
        result = await self.session.execute(
            select(MarraCampaign)
            .where(MarraCampaign.is_active.is_(True))
            .order_by(MarraCampaign.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        title: str,
        description: Optional[str],
        prize_text: Optional[str],
        book_title: str,
        book_text: str,
        day_count: int,
        daily_minutes_required: int,
        start_date: date,
        book_cover_file_id: Optional[str] = None,
    ) -> MarraCampaign:
        campaign = MarraCampaign(
            title=title,
            description=description,
            prize_text=prize_text,
            book_title=book_title,
            book_text=book_text,
            day_count=day_count,
            daily_minutes_required=daily_minutes_required,
            start_date=start_date,
            book_cover_file_id=book_cover_file_id,
        )
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def set_active(self, campaign: MarraCampaign, is_active: bool) -> None:
        campaign.is_active = is_active
        await self.session.flush()
