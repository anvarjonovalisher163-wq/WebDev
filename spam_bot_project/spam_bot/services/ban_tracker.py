import time

_TTL_SECONDS = 30

# (chat_id, user_id) -> bot tomonidan bloklangan vaqt (monotonic).
# Telegram "X guruhdan chiqarildi" tizim xabarini avtomatik yaratadi;
# buni faqat BIZNING bot bloklagan hollarda o'chirish uchun ishlatiladi.
_recent_bans: dict[tuple[int, int], float] = {}


def mark_banned(chat_id: int, user_id: int) -> None:
    _recent_bans[(chat_id, user_id)] = time.monotonic()


def was_recently_banned(chat_id: int, user_id: int) -> bool:
    timestamp = _recent_bans.pop((chat_id, user_id), None)
    if timestamp is None:
        return False
    return time.monotonic() - timestamp <= _TTL_SECONDS
