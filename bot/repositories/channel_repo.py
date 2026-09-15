from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.channel import MandatoryChannel


class ChannelRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> list[MandatoryChannel]:
        result = await self.session.execute(
            select(MandatoryChannel)
            .where(MandatoryChannel.is_active.is_(True))
            .order_by(MandatoryChannel.position)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[MandatoryChannel]:
        result = await self.session.execute(
            select(MandatoryChannel).order_by(MandatoryChannel.position)
        )
        return list(result.scalars().all())

    async def add(
        self,
        title: str,
        chat_id: int,
        username: str | None,
        invite_url: str | None,
    ) -> MandatoryChannel:
        max_position = await self.session.execute(select(MandatoryChannel.position))
        positions = [p for p in max_position.scalars().all()]
        channel = MandatoryChannel(
            title=title,
            chat_id=chat_id,
            username=username,
            invite_url=invite_url,
            position=(max(positions) + 1) if positions else 0,
        )
        self.session.add(channel)
        await self.session.flush()
        return channel

    async def delete(self, channel: MandatoryChannel) -> None:
        await self.session.delete(channel)

    async def get_by_id(self, channel_id: int) -> MandatoryChannel | None:
        return await self.session.get(MandatoryChannel, channel_id)
