from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class UserIdentity(Base):
    """Bitta UCHQUN hisobiga (har doim Telegram orqali ro'yxatdan o'tgan
    `User`ga) bog'langan qo'shimcha kirish usuli - Google/Apple uchun
    ularning "sub" identifikatori, email/telefon uchun o'zi. Bular hech
    qachon YANGI hisob ochmaydi - faqat allaqachon mavjud hisobga
    qo'shimcha kirish yo'li sifatida bog'lanadi."""

    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_user_identity_provider_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    provider: Mapped[str] = mapped_column(String(32))  # google | apple | email | phone
    external_id: Mapped[str] = mapped_column(String(255))  # sub / email / telefon

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthFlowState(Base):
    """Email/telefon OTP kodlari va OAuth (Google/Apple) 'state' qiymatlari
    uchun umumiy, tez eskiruvchi vaqtinchalik holat jadvali."""

    __tablename__ = "auth_flow_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))  # otp_email | otp_phone | oauth_google | oauth_apple
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linking_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    next_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
