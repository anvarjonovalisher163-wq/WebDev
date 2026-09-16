import sys

from loguru import logger

from spam_bot.config import settings


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, colorize=True)
    logger.add(
        "logs/spam_bot.log",
        level="WARNING",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )
