from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.models.payment_log import PaymentLog


class PaymentLogRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, chat_id: int, payer_id: int, stars_amount: int) -> PaymentLog:
        row = PaymentLog(chat_id=chat_id, payer_id=payer_id, stars_amount=stars_amount)
        self.session.add(row)
        await self.session.flush()
        return row

    async def total_stars_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(PaymentLog.stars_amount), 0)).where(PaymentLog.created_at >= since)
        )
        return int(result.scalar_one())
