import secrets
import time
from dataclasses import dataclass

_TOKEN_TTL_SECONDS = 15 * 60


@dataclass
class PendingKeyRequest:
    chat_id: int
    admin_id: int
    expires_at: float


class KeyLinkService:
    """Guruhning Gemini kalitini kiritish uchun bir martalik, muddatli havola.

    Kalitning o'zi hech qachon Telegram xabarlarida ko'rinmasligi uchun admin
    shaxsiy HTTPS shaklga yo'naltiriladi; token faqat xotirada saqlanadi va
    ishlatilgach yoki muddati o'tgach o'chiriladi.
    """

    def __init__(self) -> None:
        self._pending: dict[str, PendingKeyRequest] = {}

    def create_token(self, chat_id: int, admin_id: int) -> str:
        self._cleanup_expired()
        token = secrets.token_urlsafe(32)
        self._pending[token] = PendingKeyRequest(chat_id, admin_id, time.monotonic() + _TOKEN_TTL_SECONDS)
        return token

    def consume(self, token: str) -> PendingKeyRequest | None:
        self._cleanup_expired()
        return self._pending.pop(token, None)

    def peek(self, token: str) -> PendingKeyRequest | None:
        self._cleanup_expired()
        return self._pending.get(token)

    def _cleanup_expired(self) -> None:
        now = time.monotonic()
        expired = [t for t, req in self._pending.items() if req.expires_at <= now]
        for t in expired:
            self._pending.pop(t, None)


key_link_service = KeyLinkService()
