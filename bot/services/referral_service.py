from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.channel import MandatoryChannel
from bot.models.referral import Referral, ReferralStatus
from bot.models.user import User
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.user_repo import UserRepo
from bot.services.subscription_service import SubscriptionService


class ReferralService:
    def __init__(self, session: AsyncSession, subscription_service: SubscriptionService):
        self.session = session
        self.referral_repo = ReferralRepo(session)
        self.user_repo = UserRepo(session)
        self.subscription_service = subscription_service

    def pick_valid_referrer(self, new_user_tg_id: int, referrer: Optional[User]) -> Optional[User]:
        """4.3-bo'lim: o'z-o'ziga referral va bloklangan referrer hisoblanmaydi."""
        if referrer is None:
            return None
        if referrer.tg_id == new_user_tg_id:
            return None
        if referrer.is_blocked:
            return None
        return referrer

    async def register_referral(self, referrer: User, referred: User, season_id: int) -> Referral:
        return await self.referral_repo.create_pending(referrer.id, referred.id, season_id)

    async def try_confirm(
        self, referral: Referral, referred_user: User, channels: list[MandatoryChannel]
    ) -> bool:
        """Referred foydalanuvchi barcha majburiy kanallarga obuna bo'lsa, referralni tasdiqlaydi."""
        if referral.status != ReferralStatus.PENDING:
            return referral.status == ReferralStatus.APPROVED

        not_subscribed = await self.subscription_service.get_not_subscribed(
            referred_user.tg_id, channels
        )
        if not_subscribed:
            await self.referral_repo.touch_checked(referral)
            return False

        await self.referral_repo.approve(referral)
        return True

    async def get_progress(self, referrer_id: int, required_count: int) -> dict:
        approved = await self.referral_repo.count_by_referrer_and_status(
            referrer_id, ReferralStatus.APPROVED
        )
        pending = await self.referral_repo.count_by_referrer_and_status(
            referrer_id, ReferralStatus.PENDING
        )
        return {
            "required": required_count,
            "approved": approved,
            "pending": pending,
            "remaining": max(required_count - approved, 0),
        }

    async def recheck_approved_before_secret_link(
        self, referrer_id: int, channels: list[MandatoryChannel]
    ) -> int:
        """3.3.3 / 4.4: maxfiy havola so'ralganda barcha tasdiqlangan referrallarning
        obunasi qayta tekshiriladi; kanaldan chiqib ketganlar hisobdan chiqariladi."""
        approved_referrals = await self.referral_repo.list_approved_by_referrer(referrer_id)
        still_approved = 0
        for referral in approved_referrals:
            referred_user = await self.user_repo.get_by_id(referral.referred_id)
            if referred_user is None:
                continue
            not_subscribed = await self.subscription_service.get_not_subscribed(
                referred_user.tg_id, channels
            )
            if not_subscribed:
                await self.referral_repo.mark_left_channels(referral)
            else:
                await self.referral_repo.touch_checked(referral)
                still_approved += 1
        return still_approved
