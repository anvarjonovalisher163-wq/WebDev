from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tg_id(self, tg_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def create(
        self,
        tg_id: int,
        first_name: str,
        last_name: Optional[str],
        username: Optional[str],
        referral_code: str,
        referrer_id: Optional[int] = None,
    ) -> User:
        user = User(
            tg_id=tg_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            referral_code=referral_code,
            referrer_id=referrer_id,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def touch_profile(
        self,
        user: User,
        first_name: str,
        last_name: Optional[str],
        username: Optional[str],
    ) -> None:
        user.first_name = first_name
        user.last_name = last_name
        user.username = username

    async def list_not_blocked(self) -> list[User]:
        result = await self.session.execute(select(User).where(User.is_blocked.is_(False)))
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 10) -> list[User]:
        query = query.strip().lstrip("@")
        if query.isdigit():
            result = await self.session.execute(
                select(User).where(User.tg_id == int(query)).limit(limit)
            )
            return list(result.scalars().all())

        like = f"%{query}%"
        result = await self.session.execute(
            select(User)
            .where(
                or_(
                    User.username.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_referred_by(self, referrer_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.referrer_id == referrer_id)
        )
        return result.scalar_one()

    async def count_joined_private_channel(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.joined_private_channel.is_(True))
        )
        return result.scalar_one()

    async def count_cert_form_filled(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.cert_full_name.is_not(None))
        )
        return result.scalar_one()

    async def count_cert_issued(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.cert_issued_at.is_not(None))
        )
        return result.scalar_one()

    async def list_ready_for_certificate(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(
                User.cert_full_name.is_not(None),
                User.cert_issued_at.is_(None),
            )
        )
        return list(result.scalars().all())
