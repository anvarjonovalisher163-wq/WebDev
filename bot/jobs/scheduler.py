from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.jobs.link_expiry import expire_stale_links_job
from bot.jobs.marra_reminder import send_marra_reminders_job

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


def setup_jobs(bot: Bot) -> None:
    """Barcha davriy vazifalarni scheduler'ga ro'yxatdan o'tkazadi."""
    scheduler.add_job(
        expire_stale_links_job,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],
        id="expire_stale_links",
        replace_existing=True,
    )
    scheduler.add_job(
        send_marra_reminders_job,
        trigger=CronTrigger(minute=0),
        args=[bot],
        id="send_marra_reminders",
        replace_existing=True,
    )
