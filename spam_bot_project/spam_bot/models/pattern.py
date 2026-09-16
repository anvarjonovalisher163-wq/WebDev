from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from spam_bot.models.base import Base, TimestampMixin


class SpamPattern(Base, TimestampMixin):
    """Adminlar tomonidan o'rgatilgan, guruhga xos kalit so'z/pattern."""

    __tablename__ = "spam_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    pattern: Mapped[str] = mapped_column(String(255))
    added_by: Mapped[int] = mapped_column(BigInteger)
