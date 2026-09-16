from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.config import settings
from spam_bot.filters.is_group_admin import IsGroupAdmin
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.repositories.usage_repo import UsageRepo

router = Router(name="admin_tokens")

_PERIODS = (("kecha", 1), ("7 kun", 7), ("30 kun", 30))


def _cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * settings.gemini_price_in + (output_tokens / 1_000_000) * settings.gemini_price_out


@router.message(Command("tokens"), F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())
async def cmd_tokens(message: Message, session: AsyncSession) -> None:
    group = await GroupRepo(session).get_by_chat_id(message.chat.id)
    if group is None:
        await message.answer("Bu guruh uchun ma'lumot topilmadi. Avval /enable buyrug'ini bering.")
        return

    usage_repo = UsageRepo(session)
    lines = ["📊 <b>Gemini tokenlaridan foydalanish</b>"]
    now = datetime.now(timezone.utc)
    for label, days in _PERIODS:
        since = now - timedelta(days=days)
        input_tokens, output_tokens = await usage_repo.totals_since(group.chat_id, since)
        cost = _cost(input_tokens, output_tokens)
        lines.append(f"• {label}: {input_tokens + output_tokens} token (${cost:.4f})")
    if not group.gemini_key_encrypted:
        lines.append("\nℹ️ Bu guruh uchun Gemini kaliti sozlanmagan — AI qatlami ishlamayapti.")
    await message.answer("\n".join(lines))
