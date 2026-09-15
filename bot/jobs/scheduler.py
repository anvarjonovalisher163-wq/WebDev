from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Fon vazifalar (link muddati tugashini belgilash, kunlik hisobot va h.k.)
# keyingi bosqichlarda shu yerga qo'shiladi.
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


def setup_jobs(bot) -> None:
    """Barcha davriy vazifalarni scheduler'ga ro'yxatdan o'tkazadi."""
    pass
