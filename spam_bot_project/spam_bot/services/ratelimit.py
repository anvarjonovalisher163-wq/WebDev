import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    """Har bir chat uchun bir daqiqalik oynada nechta so'rovga ruxsat borligini nazorat qiladi.

    Gemini so'rovlari xarajat qilgani uchun har bir shubhali xabar AI'ga
    yuborilavermaydi, balki chatga xos limit bilan cheklanadi.
    """

    def __init__(self, max_per_minute: int = 20) -> None:
        self._max_per_minute = max_per_minute
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, chat_id: int) -> bool:
        now = time.monotonic()
        window = self._hits[chat_id]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self._max_per_minute:
            return False
        window.append(now)
        return True
