from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models.channel import MandatoryChannel

CB_CHECK_SUBSCRIPTION = "check_subscription"
CB_MENU_INVITE = "menu:invite"
CB_MENU_MY_REFERRALS = "menu:my_referrals"
CB_MENU_SECRET_LINK = "menu:secret_link"


def subscription_gate_keyboard(channels: list[MandatoryChannel]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        url = channel.invite_url or (f"https://t.me/{channel.username}" if channel.username else None)
        if url:
            rows.append([InlineKeyboardButton(text=channel.title, url=url)])
    rows.append([InlineKeyboardButton(text="Obunani tekshirish", callback_data=CB_CHECK_SUBSCRIPTION)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Taklif qilish", callback_data=CB_MENU_INVITE),
                InlineKeyboardButton(text="Mening takliflarim", callback_data=CB_MENU_MY_REFERRALS),
            ],
            [InlineKeyboardButton(text="Maxfiy havolani olish", callback_data=CB_MENU_SECRET_LINK)],
        ]
    )
