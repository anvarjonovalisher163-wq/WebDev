from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.models.channel import MandatoryChannel

CB_CHECK_SUBSCRIPTION = "check_subscription"
CB_REFRESH_MY_REFERRALS = "refresh_my_referrals"

BTN_INVITE = "🔗 Taklif qilish"
BTN_MY_REFERRALS = "📊 Mening takliflarim"


def subscription_gate_keyboard(channels: list[MandatoryChannel]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        url = channel.invite_url or (f"https://t.me/{channel.username}" if channel.username else None)
        if url:
            rows.append([InlineKeyboardButton(text=f"📢 {channel.title}", url=url)])
    rows.append(
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data=CB_CHECK_SUBSCRIPTION)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_INVITE), KeyboardButton(text=BTN_MY_REFERRALS)]],
        resize_keyboard=True,
    )


def my_referrals_refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data=CB_REFRESH_MY_REFERRALS)]
        ]
    )
