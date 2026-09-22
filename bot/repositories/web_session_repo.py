from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.web_session import WebLoginToken, WebSession

LOGIN_TOKEN_TTL_MINUTES = 5
SESSION_TTL_DAYS = 30


class WebLoginTokenRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token_hash: str) -> WebLoginToken:
        token = WebLoginToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=LOGIN_TOKEN_TTL_MINUTES),
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_valid(self, token_hash: str) -> Optional[WebLoginToken]:
        result = await self.session.execute(
            select(WebLoginToken).where(WebLoginToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is None or token.used_at is not None:
            return None
        if token.expires_at < datetime.now(timezone.utc):
            return None
        return token

    async def mark_used(self, token: WebLoginToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self.session.flush()


class WebSessionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token_hash: str) -> WebSession:
        web_session = WebSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS),
        )
        self.session.add(web_session)
        await self.session.flush()
        return web_session

    async def get_valid(self, token_hash: str) -> Optional[WebSession]:
        result = await self.session.execute(
            select(WebSession).where(WebSession.token_hash == token_hash)
        )
        web_session = result.scalar_one_or_none()
        if web_session is None:
            return None
        if web_session.expires_at < datetime.now(timezone.utc):
            return None
        return web_session

    async def touch(self, web_session: WebSession) -> None:
        web_session.last_seen_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def revoke(self, token_hash: str) -> None:
        result = await self.session.execute(
            select(WebSession).where(WebSession.token_hash == token_hash)
        )
        web_session = result.scalar_one_or_none()
        if web_session is not None:
            await self.session.delete(web_session)
