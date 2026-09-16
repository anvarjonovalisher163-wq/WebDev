from aiogram import Dispatcher

from spam_bot.handlers.admin import router as admin_router
from spam_bot.handlers.user import router as user_router

# admin router user router'dan OLDIN ro'yxatdan o'tishi kerak: aks holda
# /ban, /mute kabi buyruqlarni moderatsiya oqimi ushlab qolmasligi kerak.
_ROUTERS: list = [admin_router, user_router]


def setup_routers(dp: Dispatcher) -> None:
    for router in _ROUTERS:
        dp.include_router(router)
