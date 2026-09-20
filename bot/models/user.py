from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)

    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="uz")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    referrer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referral_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    has_generated_link: Mapped[bool] = mapped_column(Boolean, default=False)
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    secret_link_taken: Mapped[bool] = mapped_column(Boolean, default=False)
    secret_link_attempts: Mapped[int] = mapped_column(Integer, default=0)

    joined_private_channel: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_private_channel_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    reply_menu_shown: Mapped[bool] = mapped_column(Boolean, default=False)

    cert_full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cert_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cert_issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_marra_participant: Mapped[bool] = mapped_column(Boolean, default=False)

    referrer: Mapped[Optional["User"]] = relationship(remote_side=[id])
