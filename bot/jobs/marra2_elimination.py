from datetime import datetime
from zoneinfo import ZoneInfo

from loguru import logger

from bot.db.session import async_session_factory
from bot.repositories.marra_campaign_repo import MarraCampaignRepo
from bot.repositories.marra_participant_repo import MarraParticipantRepo
from bot.repositories.marra_progress_repo import MarraProgressRepo

TASHKENT_TZ = ZoneInfo("Asia/Tashkent")


async def eliminate_marra2_stragglers_job() -> None:
    """Har kuni kechasi ishga tushadi: KECHAGI (to'liq yakunlangan) kun uchun
    kunlik o'qish talabini bajarmagan ishtirokchilarni marradan avtomatik
    chiqaradi - xuddi Mutolaa'dagi kabi (1 kun bajarilmasa, chetlatiladi)."""
    today = datetime.now(TASHKENT_TZ).date()

    async with async_session_factory() as session:
        campaign_repo = MarraCampaignRepo(session)
        participant_repo = MarraParticipantRepo(session)
        progress_repo = MarraProgressRepo(session)

        eliminated_total = 0
        for campaign in await campaign_repo.list_active():
            yesterday_day = (today - campaign.start_date).days
            if yesterday_day < 1 or yesterday_day > campaign.day_count:
                continue  # marra hali boshlanmagan yoki kunlari allaqachon tugagan

            for participant in await participant_repo.list_active_by_campaign(campaign.id):
                join_day = max(
                    (participant.joined_at.astimezone(TASHKENT_TZ).date() - campaign.start_date).days + 1,
                    1,
                )
                if join_day > yesterday_day:
                    continue  # ishtirokchi kechadan keyin qo'shilgan - hali baholanmaydi

                progress = await progress_repo.get(participant.id, yesterday_day)
                if progress is None or not progress.completed:
                    await participant_repo.eliminate(participant, yesterday_day)
                    eliminated_total += 1

        if eliminated_total:
            await session.commit()
            logger.info(
                f"Marra 2.0: {eliminated_total} ishtirokchi kunlik vazifani bajarmagani uchun chiqarildi"
            )
