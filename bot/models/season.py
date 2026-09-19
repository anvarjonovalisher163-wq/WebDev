from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    winner_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    winner_referral_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
