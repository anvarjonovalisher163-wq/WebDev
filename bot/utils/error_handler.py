from aiogram.types import ErrorEvent
from loguru import logger


def register_error_handler(dp) -> None:
    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        update = event.update
        logger.opt(exception=event.exception).error(f"Update handling xatosi: update_id={update.update_id}")
        return True
