from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.models.group import Group


class GroupRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_chat_id(self, chat_id: int) -> Group | None:
        result = await self.session.execute(select(Group).where(Group.chat_id == chat_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, chat_id: int, title: str | None, owner_id: int) -> Group:
        group = await self.get_by_chat_id(chat_id)
        if group is not None:
            return group
        group = Group(chat_id=chat_id, title=title, owner_id=owner_id, enabled=False)
        self.session.add(group)
        await self.session.flush()
        return group

    async def count_enabled_for_owner(self, owner_id: int) -> int:
        result = await self.session.execute(
            select(Group).where(Group.owner_id == owner_id, Group.enabled.is_(True))
        )
        return len(result.scalars().all())

    async def set_enabled(self, group: Group, enabled: bool) -> None:
        group.enabled = enabled
        await self.session.flush()

    async def set_gemini_key(self, group: Group, encrypted_key: str | None) -> None:
        group.gemini_key_encrypted = encrypted_key
        await self.session.flush()

    async def list_enabled(self) -> list[Group]:
        result = await self.session.execute(select(Group).where(Group.enabled.is_(True)))
        return list(result.scalars().all())
