from typing import Optional

from sqlalchemy import select
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

    async def get_by_referral_code(self, referral_code: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.referral_code == referral_code))
        return result.scalar_one_or_none()

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

    async def set_subscribed(self, user: User, is_subscribed: bool) -> None:
        user.is_subscribed = is_subscribed
