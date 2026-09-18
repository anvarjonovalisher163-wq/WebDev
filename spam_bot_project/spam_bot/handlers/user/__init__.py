from aiogram import Router

from spam_bot.handlers.user.commands import router as commands_router
from spam_bot.handlers.user.moderation_pipeline import router as moderation_pipeline_router
from spam_bot.handlers.user.subscription import router as subscription_router

router = Router(name="user")
router.include_router(commands_router)
router.include_router(subscription_router)
router.include_router(moderation_pipeline_router)
