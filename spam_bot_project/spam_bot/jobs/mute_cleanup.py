from spam_bot.db.session import async_session_factory
from spam_bot.repositories.mute_repo import MuteRepo


async def deactivate_expired_mutes_job() -> None:
    """Telegram muddati o'tgan cheklovni serverda o'zi tiklaydi; bu yerda faqat
    bazadagi yozuvni nofaol deb belgilaymiz, hisobot to'g'ri bo'lishi uchun."""
    async with async_session_factory() as session:
        repo = MuteRepo(session)
        for record in await repo.list_expired():
            await repo.deactivate(record)
        await session.commit()
