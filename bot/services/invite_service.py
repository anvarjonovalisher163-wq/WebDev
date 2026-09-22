from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.invite_link import InviteLink, InviteLinkStatus
from bot.models.season import Season
from bot.models.settings import BotSettings
from bot.models.user import User
from bot.repositories.invite_repo import InviteRepo


class InviteService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.invite_repo = InviteRepo(session)

    async def create_one_time_link(self, user: User, settings: BotSettings, season: Season) -> InviteLink:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.link_ttl_minutes)
        tg_link = await self.bot.create_chat_invite_link(
            chat_id=season.secret_channel_id,
            name=f"ref-{user.tg_id}",
            expire_date=expires_at,
            member_limit=settings.link_member_limit,
        )
        link = await self.invite_repo.create(
            user_id=user.id,
            telegram_link=tg_link.invite_link,
            expires_at=expires_at,
            member_limit=settings.link_member_limit,
            channel_id=season.secret_channel_id,
        )
        user.secret_link_taken = True
        user.secret_link_attempts += 1
        return link

    async def revoke(self, link: InviteLink, *, status: InviteLinkStatus) -> None:
        try:
            await self.bot.revoke_chat_invite_link(
                chat_id=link.channel_id, invite_link=link.telegram_link
            )
        except TelegramBadRequest:
            pass  # allaqachon bekor qilingan yoki muddati o'tgan bo'lishi mumkin
        link.status = status
        link.revoked_at = datetime.now(timezone.utc)

    async def mark_used_and_revoke(self, link: InviteLink) -> None:
        link.status = InviteLinkStatus.USED
        link.joined_at = datetime.now(timezone.utc)
        try:
            await self.bot.revoke_chat_invite_link(
                chat_id=link.channel_id, invite_link=link.telegram_link
            )
        except TelegramBadRequest:
            pass

    async def expire_stale_links(self) -> list[InviteLink]:
        expired = await self.invite_repo.list_expired_active(datetime.now(timezone.utc))
        for link in expired:
            await self.revoke(link, status=InviteLinkStatus.EXPIRED)
        return expired
