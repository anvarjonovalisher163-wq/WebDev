from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.models.channel import MandatoryChannel

CB_CHECK_SUBSCRIPTION = "check_subscription"

BTN_INVITE = "Taklif qilish"
BTN_MY_REFERRALS = "Mening takliflarim"
BTN_SECRET_LINK = "Maxfiy havolani olish"


def subscription_gate_keyboard(channels: list[MandatoryChannel]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        url = channel.invite_url or (f"https://t.me/{channel.username}" if channel.username else None)
        if url:
            rows.append([InlineKeyboardButton(text=channel.title, url=url)])
    rows.append([InlineKeyboardButton(text="Obunani tekshirish", callback_data=CB_CHECK_SUBSCRIPTION)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_INVITE), KeyboardButton(text=BTN_MY_REFERRALS)],
            [KeyboardButton(text=BTN_SECRET_LINK)],
        ],
        resize_keyboard=True,
    )
