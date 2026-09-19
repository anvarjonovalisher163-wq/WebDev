from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.referral import Referral, ReferralStatus
from bot.models.user import User


class ReferralRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_pending(self, referrer_id: int, referred_id: int, season_id: int) -> Referral:
        referral = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id,
            season_id=season_id,
            status=ReferralStatus.PENDING,
        )
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def get_by_referred_id(self, referred_id: int) -> Optional[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()

    async def list_by_referrer(self, referrer_id: int) -> list[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.referrer_id == referrer_id)
        )
        return list(result.scalars().all())

    async def list_approved_by_referrer(self, referrer_id: int) -> list[Referral]:
        result = await self.session.execute(
            select(Referral).where(
                Referral.referrer_id == referrer_id,
                Referral.status == ReferralStatus.APPROVED,
            )
        )
        return list(result.scalars().all())

    async def count_by_referrer_and_status(self, referrer_id: int, status: ReferralStatus) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Referral)
            .where(Referral.referrer_id == referrer_id, Referral.status == status)
        )
        return result.scalar_one()

    async def count_by_referrer_and_status_in_season(
        self, referrer_id: int, status: ReferralStatus, season_id: int
    ) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Referral)
            .where(
                Referral.referrer_id == referrer_id,
                Referral.status == status,
                Referral.season_id == season_id,
            )
        )
        return result.scalar_one()

    async def approve(self, referral: Referral) -> None:
        referral.status = ReferralStatus.APPROVED
        referral.approved_at = datetime.now(timezone.utc)
        referral.last_checked_at = referral.approved_at

    async def mark_left_channels(self, referral: Referral) -> None:
        referral.status = ReferralStatus.LEFT_CHANNELS
        referral.reject_reason = "majburiy kanallardan chiqib ketgan"
        referral.last_checked_at = datetime.now(timezone.utc)

    async def touch_checked(self, referral: Referral) -> None:
        referral.last_checked_at = datetime.now(timezone.utc)

    async def season_leaderboard(
        self, season_id: int, limit: Optional[int] = 10, offset: int = 0
    ) -> list[tuple[int, int]]:
        """Botdan foydalangan (bloklanmagan) BARCHA foydalanuvchilar ro'yxati:
        [(user_id, shu_mavsumda_tasdiqlangan_soni), ...], ko'p -> kam. Hech kimni
        taklif qilmaganlar ham 0 soni bilan ro'yxatda qoladi. Teng bo'lsa,
        avvalroq shu songa yetgan oldinda, undan keyin ro'yxatga avvalroq
        qo'shilgan oldinda turadi. `limit=None` - hammasini qaytaradi."""
        counts = (
            select(
                Referral.referrer_id.label("referrer_id"),
                func.count().label("cnt"),
                func.min(Referral.approved_at).label("first_approved"),
            )
            .where(Referral.season_id == season_id, Referral.status == ReferralStatus.APPROVED)
            .group_by(Referral.referrer_id)
            .subquery()
        )
        query = (
            select(
                User.id.label("user_id"),
                func.coalesce(counts.c.cnt, 0).label("cnt"),
            )
            .select_from(User)
            .outerjoin(counts, counts.c.referrer_id == User.id)
            .where(User.is_blocked.is_(False))
            .order_by(
                func.coalesce(counts.c.cnt, 0).desc(),
                counts.c.first_approved.asc().nulls_last(),
                User.created_at.asc(),
            )
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [(row.user_id, row.cnt) for row in result.all()]

    async def season_participant_count(self, season_id: int) -> int:
        """Botdan foydalanadigan (bloklanmagan) barcha foydalanuvchilar soni -
        reytingda ko'rsatiladiganlarning umumiy soni."""
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_blocked.is_(False))
        )
        return result.scalar_one()

    async def season_rank_of(self, season_id: int, referrer_id: int) -> Optional[tuple[int, int]]:
        """(o'rin, soni) - foydalanuvchi bloklangan bo'lsa None."""
        rows = await self.season_leaderboard(season_id, limit=None)
        for index, (user_id, cnt) in enumerate(rows, start=1):
            if user_id == referrer_id:
                return index, cnt
        return None
