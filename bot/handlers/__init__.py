from aiogram import Dispatcher

from bot.handlers.admin import router as admin_router
from bot.handlers.user import router as user_router

# admin router user router'dan OLDIN ro'yxatdan o'tishi kerak:
# aks holda /admin buyrug'ini oddiy foydalanuvchi handler'lari ushlab qolishi mumkin.
_ROUTERS: list = [admin_router, user_router]


def setup_routers(dp: Dispatcher) -> None:
    for router in _ROUTERS:
        dp.include_router(router)
