import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CANCELLED = "cancelled"
    FRAUD = "fraud"
    LEFT_CHANNELS = "left_channels"


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        # bitta foydalanuvchi faqat bitta taklif qiluvchiga biriktiriladi
        UniqueConstraint("referred_id", name="uq_referrals_referred_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    referrer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referred_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    season_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seasons.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, name="referral_status"), default=ReferralStatus.PENDING, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    reject_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
