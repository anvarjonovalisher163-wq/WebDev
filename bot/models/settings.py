from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class BotSettings(Base):
    """Bitta qatordan iborat (singleton, id=1) global sozlamalar jadvali."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    welcome_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    welcome_media_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    welcome_media_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # photo/video

    referral_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referral_image_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    share_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    subscription_gate_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    required_referral_count: Mapped[int] = mapped_column(Integer, default=5)

    link_ttl_minutes: Mapped[int] = mapped_column(Integer, default=30)
    link_member_limit: Mapped[int] = mapped_column(Integer, default=1)

    reissue_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    max_reissue_attempts: Mapped[int] = mapped_column(Integer, default=3)

    acceptance_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    certificate_body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_signature_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
