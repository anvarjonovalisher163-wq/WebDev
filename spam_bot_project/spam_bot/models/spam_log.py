from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spam_bot.models.base import Base, TimestampMixin


class SpamLog(Base, TimestampMixin):
    """Aniqlangan har bir spam holati bo'yicha yozuv (hisobot va o'quv uchun)."""

    __tablename__ = "spam_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(String(32))  # keyword | ai | nsfw | malware_link | raid
    action: Mapped[str] = mapped_column(String(16))  # delete | mute | ban
