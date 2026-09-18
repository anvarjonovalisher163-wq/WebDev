from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.filters.is_operator import IsOperator
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.repositories.payment_log_repo import PaymentLogRepo
from spam_bot.repositories.spam_log_repo import SpamLogRepo

router = Router(name="admin_stats")


@router.message(Command("stats"), F.chat.type == "private", IsOperator())
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    group_repo = GroupRepo(session)
    spam_repo = SpamLogRepo(session)

    enabled_groups = await group_repo.list_enabled()
    now = datetime.now(timezone.utc)
    day_count = await spam_repo.count_total_since(now - timedelta(days=1))
    week_count = await spam_repo.count_total_since(now - timedelta(days=7))

    lines = [
        "📈 <b>Statistika</b>",
        f"Faol guruhlar: {len(enabled_groups)}",
        f"Tutilgan spam (24 soat): {day_count}",
        f"Tutilgan spam (7 kun): {week_count}",
    ]
    if enabled_groups:
        lines.append("\n<b>Guruhlar:</b>")
        for group in enabled_groups[:30]:
            title = group.title or str(group.chat_id)
            group_day = await spam_repo.count_for_chat(group.chat_id, now - timedelta(days=1))
            lines.append(f"• {title} — {group_day} (24s)")
    await message.answer("\n".join(lines))


@router.message(Command("daromad"), F.chat.type == "private", IsOperator())
async def cmd_daromad(message: Message, session: AsyncSession) -> None:
    payment_repo = PaymentLogRepo(session)
    now = datetime.now(timezone.utc)
    week_total = await payment_repo.total_stars_since(now - timedelta(days=7))
    month_total = await payment_repo.total_stars_since(now - timedelta(days=30))
    lines = [
        "💰 <b>Daromad (Telegram Stars)</b>",
        f"So'nggi 7 kun: {week_total} ⭐",
        f"So'nggi 30 kun: {month_total} ⭐",
        "\nStars'ni pulga aylantirish uchun: https://fragment.com",
    ]
    await message.answer("\n".join(lines))
