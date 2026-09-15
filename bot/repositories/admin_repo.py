from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.admin import Admin


class AdminRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tg_id(self, tg_id: int) -> Optional[Admin]:
        result = await self.session.execute(select(Admin).where(Admin.tg_id == tg_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Admin]:
        result = await self.session.execute(select(Admin).order_by(Admin.created_at))
        return list(result.scalars().all())

    async def add(self, tg_id: int, is_super_admin: bool = False, added_by: Optional[int] = None) -> Admin:
        admin = Admin(tg_id=tg_id, is_super_admin=is_super_admin, added_by=added_by)
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def remove(self, admin: Admin) -> None:
        await self.session.delete(admin)

    async def ensure_super_admins(self, tg_ids: list[int]) -> None:
        for tg_id in tg_ids:
            existing = await self.get_by_tg_id(tg_id)
            if existing is None:
                await self.add(tg_id, is_super_admin=True)
            elif not existing.is_super_admin:
                existing.is_super_admin = True
