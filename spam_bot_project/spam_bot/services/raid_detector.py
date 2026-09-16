import hashlib
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field

_WINDOW_SECONDS = 120
_MIN_DISTINCT_USERS = 3
_NORMALIZE_RE = re.compile(r"[^\w]+", re.UNICODE)


def _fingerprint(text: str) -> str:
    normalized = _NORMALIZE_RE.sub("", text.lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class _Sighting:
    user_id: int
    timestamp: float


@dataclass
class _ChatState:
    by_fingerprint: dict[str, list[_Sighting]] = field(default_factory=dict)


class RaidDetector:
    """Bir necha akkountdan qisqa vaqt ichida kelgan bir xil xabarlarni aniqlaydi.

    Xotirada saqlanadi (Redis shart emas): har bir jarayon o'z nusxasini
    kuzatadi, bu bitta bot instansi uchun yetarli.
    """

    def __init__(self, window_seconds: int = _WINDOW_SECONDS, min_distinct_users: int = _MIN_DISTINCT_USERS) -> None:
        self._window = window_seconds
        self._min_distinct_users = min_distinct_users
        self._chats: dict[int, _ChatState] = defaultdict(_ChatState)

    def register(self, chat_id: int, user_id: int, text: str) -> list[int] | None:
        """Xabarni ro'yxatga oladi; agar hujum aniqlansa, aloqador user_id'lar ro'yxatini qaytaradi."""
        if not text or len(text.strip()) < 5:
            return None

        now = time.monotonic()
        state = self._chats[chat_id]
        fp = _fingerprint(text)
        sightings = state.by_fingerprint.setdefault(fp, [])

        sightings[:] = [s for s in sightings if now - s.timestamp <= self._window]
        if not any(s.user_id == user_id for s in sightings):
            sightings.append(_Sighting(user_id, now))

        distinct_users = {s.user_id for s in sightings}
        if len(distinct_users) >= self._min_distinct_users:
            state.by_fingerprint.pop(fp, None)
            return list(distinct_users)
        return None


raid_detector = RaidDetector()
