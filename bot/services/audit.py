from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.admin_log import AdminLog


async def log_admin_action(
    session: AsyncSession, admin_tg_id: int, action: str, details: Optional[str] = None
) -> None:
    session.add(AdminLog(admin_tg_id=admin_tg_id, action=action, details=details))
