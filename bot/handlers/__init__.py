from aiogram import Dispatcher

# Handler routerlari keyingi bosqichlarda shu yerga qo'shiladi
# (user/start, user/subscription, admin/panel, ...).
_ROUTERS: list = []


def setup_routers(dp: Dispatcher) -> None:
    for router in _ROUTERS:
        dp.include_router(router)
