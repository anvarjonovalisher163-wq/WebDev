from datetime import datetime, timezone
from typing import NamedTuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService

REFERRAL_PAYLOAD_PREFIX = "ref_"


class StartResult(NamedTuple):
    user: User
    is_new: bool


def build_referral_link(bot_username: str, tg_id: int) -> str:
    return f"https://t.me/{bot_username}?start={REFERRAL_PAYLOAD_PREFIX}{tg_id}"


def parse_referrer_tg_id(start_payload: Optional[str]) -> Optional[int]:
    if not start_payload or not start_payload.startswith(REFERRAL_PAYLOAD_PREFIX):
        return None
    raw_id = start_payload[len(REFERRAL_PAYLOAD_PREFIX):]
    if not raw_id.isdigit():
        return None
    return int(raw_id)


class UserService:
    def __init__(self, session: AsyncSession, referral_service: ReferralService):
        self.session = session
        self.user_repo = UserRepo(session)
        self.referral_service = referral_service

    async def register_or_touch(
        self,
        tg_id: int,
        first_name: str,
        last_name: Optional[str],
        username: Optional[str],
        start_payload: Optional[str],
    ) -> StartResult:
        existing = await self.user_repo.get_by_tg_id(tg_id)
        if existing is not None:
            await self.user_repo.touch_profile(existing, first_name, last_name, username)
            existing.last_active_at = datetime.now(timezone.utc)
            return StartResult(user=existing, is_new=False)

        referrer = None
        referrer_tg_id = parse_referrer_tg_id(start_payload)
        if referrer_tg_id is not None:
            candidate = await self.user_repo.get_by_tg_id(referrer_tg_id)
            referrer = self.referral_service.pick_valid_referrer(tg_id, candidate)

        new_user = await self.user_repo.create(
            tg_id=tg_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            referral_code=str(tg_id),
            referrer_id=referrer.id if referrer else None,
        )

        if referrer is not None:
            await self.referral_service.register_referral(referrer, new_user)

        return StartResult(user=new_user, is_new=True)
