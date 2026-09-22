from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class MarraCampaign(Base):
    """UCHQUN 2.0 - o'zimizning tizimimizdagi Marra (o'qish marafoni) kampaniyasi.
    Eski (1.0) Mutolaa-havola asosidagi marra tizimidan (settings.marra_url va
    h.k.) butunlay mustaqil - hozircha faqat admin ko'ra oladigan, hech qayerdan
    link berilmagan yangi tizim."""

    __tablename__ = "marra_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prize_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    book_title: Mapped[str] = mapped_column(String(255))
    book_cover_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    book_text: Mapped[str] = mapped_column(Text)

    day_count: Mapped[int] = mapped_column(Integer)
    daily_minutes_required: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarraParticipant(Base):
    __tablename__ = "marra_participants"
    __table_args__ = (UniqueConstraint("campaign_id", "user_id", name="uq_marra_participant"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("marra_campaigns.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_eliminated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    eliminated_on_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class MarraDailyProgress(Base):
    __tablename__ = "marra_daily_progress"
    __table_args__ = (
        UniqueConstraint("participant_id", "day_number", name="uq_marra_daily_progress"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("marra_participants.id", ondelete="CASCADE"), index=True
    )
    day_number: Mapped[int] = mapped_column(Integer)

    seconds_read: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
