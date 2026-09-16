from aiogram import Router

from bot.handlers.user.channel_events import router as channel_events_router
from bot.handlers.user.menu import router as menu_router
from bot.handlers.user.start import router as start_router
from bot.handlers.user.subscription import router as subscription_router

router = Router(name="user")
router.include_router(start_router)
router.include_router(subscription_router)
router.include_router(menu_router)
router.include_router(channel_events_router)
