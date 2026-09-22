from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user_identity import UserIdentity


class UserIdentityRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, provider: str, external_id: str) -> Optional[UserIdentity]:
        result = await self.session.execute(
            select(UserIdentity).where(
                UserIdentity.provider == provider, UserIdentity.external_id == external_id
            )
        )
        return result.scalar_one_or_none()

    async def link(self, user_id: int, provider: str, external_id: str) -> UserIdentity:
        identity = UserIdentity(user_id=user_id, provider=provider, external_id=external_id)
        self.session.add(identity)
        await self.session.flush()
        return identity

    async def list_by_user(self, user_id: int) -> list[UserIdentity]:
        result = await self.session.execute(
            select(UserIdentity).where(UserIdentity.user_id == user_id)
        )
        return list(result.scalars().all())
