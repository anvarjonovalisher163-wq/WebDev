from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.referral import Referral, ReferralStatus
from bot.models.user import User


class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count_users(self, *filters) -> int:
        result = await self.session.execute(select(func.count()).select_from(User).where(*filters))
        return result.scalar_one()

    async def _count_referrals(self, *filters) -> int:
        result = await self.session.execute(select(func.count()).select_from(Referral).where(*filters))
        return result.scalar_one()

    async def general_stats(self, required_referral_count: int) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        completed_subq = (
            select(Referral.referrer_id)
            .where(Referral.status == ReferralStatus.APPROVED)
            .group_by(Referral.referrer_id)
            .having(func.count() >= required_referral_count)
            .subquery()
        )
        completed_result = await self.session.execute(select(func.count()).select_from(completed_subq))

        distinct_referrers_result = await self.session.execute(
            select(func.count(func.distinct(Referral.referrer_id)))
        )

        return {
            "total_users": await self._count_users(),
            "today_users": await self._count_users(User.created_at >= today_start),
            "last_7d_users": await self._count_users(User.created_at >= now - timedelta(days=7)),
            "last_30d_users": await self._count_users(User.created_at >= now - timedelta(days=30)),
            "subscribed": await self._count_users(User.is_subscribed.is_(True)),
            "generated_link": await self._count_users(User.has_generated_link.is_(True)),
            "at_least_one_referral": distinct_referrers_result.scalar_one(),
            "completed_all_requirements": completed_result.scalar_one(),
            "secret_link_taken": await self._count_users(User.secret_link_taken.is_(True)),
            "joined_private": await self._count_users(User.joined_private_channel.is_(True)),
            "blocked": await self._count_users(User.is_blocked.is_(True)),
        }

    async def referral_stats(self) -> dict:
        total = await self._count_referrals()
        approved = await self._count_referrals(Referral.status == ReferralStatus.APPROVED)
        pending = await self._count_referrals(Referral.status == ReferralStatus.PENDING)
        conversion = round((approved / total * 100), 1) if total else 0.0
        return {"total": total, "approved": approved, "pending": pending, "conversion_pct": conversion}

    async def top_referrers(self, limit: int = 10) -> list[tuple[User, int]]:
        result = await self.session.execute(
            select(Referral.referrer_id, func.count().label("cnt"))
            .where(Referral.status == ReferralStatus.APPROVED)
            .group_by(Referral.referrer_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        pairs = []
        for referrer_id, cnt in result.all():
            user = await self.session.get(User, referrer_id)
            if user is not None:
                pairs.append((user, cnt))
        return pairs

    @staticmethod
    def conversion_funnel(general: dict) -> dict:
        def pct(numerator: int, denominator: int) -> float:
            return round((numerator / denominator * 100), 1) if denominator else 0.0

        return {
            "start_to_subscribed": pct(general["subscribed"], general["total_users"]),
            "subscribed_to_link": pct(general["generated_link"], general["subscribed"]),
            "link_to_completed": pct(general["completed_all_requirements"], general["generated_link"]),
            "completed_to_secret": pct(general["secret_link_taken"], general["completed_all_requirements"]),
            "secret_to_joined": pct(general["joined_private"], general["secret_link_taken"]),
        }
