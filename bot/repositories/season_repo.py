from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.season import Season

FIRST_SEASON_NAME = "1-mavsum"


class SeasonRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active(self) -> Season:
        result = await self.session.execute(select(Season).where(Season.is_active.is_(True)))
        season = result.scalar_one_or_none()
        if season is None:
            season = Season(number=1, name=FIRST_SEASON_NAME, is_active=True)
            self.session.add(season)
            await self.session.flush()
        return season

    async def get_by_id(self, season_id: int) -> Optional[Season]:
        return await self.session.get(Season, season_id)

    async def list_all(self) -> list[Season]:
        result = await self.session.execute(select(Season).order_by(Season.number.desc()))
        return list(result.scalars().all())

    async def close_and_start_next(
        self,
        closing: Season,
        winner_user_id: Optional[int],
        winner_referral_count: Optional[int],
        new_season_name: str,
    ) -> Season:
        """Joriy mavsumni yopadi va admin kiritgan nom bilan yangi mavsumni
        boshlaydi. `number` faqat ichki tartiblash uchun avtomatik oshadi -
        admin xohlagan nomni (masalan, yana "1-mavsum") erkin tanlashi mumkin."""
        closing.is_active = False
        closing.ended_at = datetime.now(timezone.utc)
        closing.winner_user_id = winner_user_id
        closing.winner_referral_count = winner_referral_count

        next_season = Season(number=closing.number + 1, name=new_season_name, is_active=True)
        self.session.add(next_season)
        await self.session.flush()
        return next_season
