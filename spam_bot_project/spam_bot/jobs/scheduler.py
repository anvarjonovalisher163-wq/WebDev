from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from spam_bot.config import settings
from spam_bot.jobs.daily_report import send_daily_report_job
from spam_bot.jobs.mute_cleanup import deactivate_expired_mutes_job
from spam_bot.jobs.retention import purge_old_records_job

scheduler = AsyncIOScheduler(timezone=settings.tz)


def setup_jobs(bot: Bot) -> None:
    """Barcha davriy vazifalarni scheduler'ga ro'yxatdan o'tkazadi."""
    scheduler.add_job(
        deactivate_expired_mutes_job,
        trigger=IntervalTrigger(minutes=5),
        id="deactivate_expired_mutes",
        replace_existing=True,
    )
    scheduler.add_job(
        purge_old_records_job,
        trigger=IntervalTrigger(hours=24),
        id="purge_old_records",
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_report_job,
        trigger=CronTrigger(hour=settings.report_hour, minute=0),
        args=[bot],
        id="send_daily_report",
        replace_existing=True,
    )
