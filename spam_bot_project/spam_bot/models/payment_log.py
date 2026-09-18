from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from spam_bot.models.base import Base, TimestampMixin


class PaymentLog(Base, TimestampMixin):
    """Telegram Stars orqali qabul qilingan har bir to'lov yozuvi (/daromad hisoboti uchun)."""

    __tablename__ = "payment_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    payer_id: Mapped[int] = mapped_column(BigInteger)
    stars_amount: Mapped[int] = mapped_column(Integer)
