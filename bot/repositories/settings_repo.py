from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.settings import BotSettings

SETTINGS_ID = 1


class SettingsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> BotSettings:
        result = await self.session.execute(select(BotSettings).where(BotSettings.id == SETTINGS_ID))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = BotSettings(id=SETTINGS_ID)
            self.session.add(settings)
            await self.session.flush()
        return settings
