from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from spam_bot.models.base import Base, TimestampMixin


class UsageLog(Base, TimestampMixin):
    """Har bir Gemini so'rovi bo'yicha token sarfi (/tokens hisoboti uchun)."""

    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
