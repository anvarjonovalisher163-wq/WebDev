from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.invite_link import InviteLink, InviteLinkStatus


class InviteRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        telegram_link: str,
        expires_at: datetime,
        member_limit: int,
        channel_id: int,
    ) -> InviteLink:
        link = InviteLink(
            user_id=user_id,
            telegram_link=telegram_link,
            expires_at=expires_at,
            member_limit=member_limit,
            channel_id=channel_id,
            status=InviteLinkStatus.ACTIVE,
        )
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_by_link(self, telegram_link: str) -> Optional[InviteLink]:
        result = await self.session.execute(
            select(InviteLink).where(InviteLink.telegram_link == telegram_link)
        )
        return result.scalar_one_or_none()

    async def get_active_for_user(self, user_id: int) -> Optional[InviteLink]:
        result = await self.session.execute(
            select(InviteLink).where(
                InviteLink.user_id == user_id,
                InviteLink.status == InviteLinkStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def list_expired_active(self, now: datetime) -> list[InviteLink]:
        result = await self.session.execute(
            select(InviteLink).where(
                InviteLink.status == InviteLinkStatus.ACTIVE,
                InviteLink.expires_at < now,
            )
        )
        return list(result.scalars().all())
