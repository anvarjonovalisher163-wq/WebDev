from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user_identity import AuthFlowState

OTP_TTL_MINUTES = 10
OAUTH_STATE_TTL_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


class AuthFlowRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        kind: str,
        token_hash: str,
        address: Optional[str] = None,
        linking_user_id: Optional[int] = None,
        next_path: Optional[str] = None,
        ttl_minutes: int = OTP_TTL_MINUTES,
    ) -> AuthFlowState:
        state = AuthFlowState(
            kind=kind,
            token_hash=token_hash,
            address=address,
            linking_user_id=linking_user_id,
            next_path=next_path,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
        )
        self.session.add(state)
        await self.session.flush()
        return state

    async def get_valid(self, kind: str, token_hash: str) -> Optional[AuthFlowState]:
        result = await self.session.execute(
            select(AuthFlowState).where(
                AuthFlowState.kind == kind, AuthFlowState.token_hash == token_hash
            )
        )
        state = result.scalar_one_or_none()
        if state is None or state.used_at is not None:
            return None
        if state.expires_at < datetime.now(timezone.utc):
            return None
        return state

    async def get_active_by_address(self, kind: str, address: str) -> Optional[AuthFlowState]:
        """OTP kodi tekshirilayotganda - telefon/email bo'yicha oxirgi
        ishlatilmagan, muddati o'tmagan holatni topadi."""
        result = await self.session.execute(
            select(AuthFlowState)
            .where(
                AuthFlowState.kind == kind,
                AuthFlowState.address == address,
                AuthFlowState.used_at.is_(None),
                AuthFlowState.expires_at > datetime.now(timezone.utc),
            )
            .order_by(AuthFlowState.created_at.desc())
        )
        return result.scalars().first()

    async def mark_used(self, state: AuthFlowState) -> None:
        state.used_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def increment_attempts(self, state: AuthFlowState) -> int:
        state.attempts += 1
        await self.session.flush()
        return state.attempts
