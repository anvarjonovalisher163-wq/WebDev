from aiogram import Router

from bot.filters.is_admin import IsAdmin
from bot.handlers.admin.admins import router as admins_router
from bot.handlers.admin.broadcast import router as broadcast_router
from bot.handlers.admin.channels import router as channels_router
from bot.handlers.admin.panel import router as panel_router
from bot.handlers.admin.referral_content import router as referral_content_router
from bot.handlers.admin.requirements import router as requirements_router
from bot.handlers.admin.search import router as search_router
from bot.handlers.admin.secret_channel import router as secret_channel_router
from bot.handlers.admin.stats import router as stats_router
from bot.handlers.admin.welcome import router as welcome_router

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.include_router(panel_router)
router.include_router(welcome_router)
router.include_router(channels_router)
router.include_router(referral_content_router)
router.include_router(requirements_router)
router.include_router(secret_channel_router)
router.include_router(broadcast_router)
router.include_router(stats_router)
router.include_router(search_router)
router.include_router(admins_router)
