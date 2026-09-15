from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from bot.models.channel import MandatoryChannel

_MEMBER_STATUSES = {"member", "administrator", "creator"}


class SubscriptionService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def is_member(self, tg_id: int, channel: MandatoryChannel) -> bool:
        try:
            member = await self.bot.get_chat_member(chat_id=channel.chat_id, user_id=tg_id)
        except TelegramBadRequest:
            # bot kanalda admin emas yoki foydalanuvchi hech qachon ko'rinmagan
            return False
        return member.status in _MEMBER_STATUSES

    async def get_not_subscribed(
        self, tg_id: int, channels: list[MandatoryChannel]
    ) -> list[MandatoryChannel]:
        not_subscribed = []
        for channel in channels:
            if not await self.is_member(tg_id, channel):
                not_subscribed.append(channel)
        return not_subscribed
