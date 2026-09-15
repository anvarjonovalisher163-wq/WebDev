from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.admin_repo import AdminRepo


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user = event.from_user
        if user is None:
            return False
        admin = await AdminRepo(session).get_by_tg_id(user.id)
        return admin is not None


class IsSuperAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user = event.from_user
        if user is None:
            return False
        admin = await AdminRepo(session).get_by_tg_id(user.id)
        return admin is not None and admin.is_super_admin
