from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spam_bot.models.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int] = mapped_column(BigInteger)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Fernet bilan shifrlangan Gemini API kaliti; kalit bo'lmasa faqat
    # kalit so'z qatlami ishlaydi.
    gemini_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Bepul sinov muddati yoki to'langan obuna qachon tugashi. None bo'lsa
    # (masalan bu funksiya qo'shilishidan oldin yaratilgan guruh) cheklovsiz
    # hisoblanadi.
    access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
