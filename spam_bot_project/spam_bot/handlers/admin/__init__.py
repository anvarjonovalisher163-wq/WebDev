from aiogram import Router

from spam_bot.handlers.admin.groups import router as groups_router
from spam_bot.handlers.admin.moderation import router as moderation_router
from spam_bot.handlers.admin.moderation_callbacks import router as moderation_callbacks_router
from spam_bot.handlers.admin.stats import router as stats_router
from spam_bot.handlers.admin.tokens import router as tokens_router

router = Router(name="admin")
router.include_router(moderation_router)
router.include_router(moderation_callbacks_router)
router.include_router(stats_router)
router.include_router(tokens_router)
router.include_router(groups_router)
