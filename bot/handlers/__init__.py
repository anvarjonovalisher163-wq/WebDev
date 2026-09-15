from aiogram import Dispatcher

from bot.handlers.user import router as user_router

# admin router keyingi bosqichda shu yerga qo'shiladi
_ROUTERS: list = [user_router]


def setup_routers(dp: Dispatcher) -> None:
    for router in _ROUTERS:
        dp.include_router(router)
