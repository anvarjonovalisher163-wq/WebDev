from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models.channel import MandatoryChannel

CB_CHECK_SUBSCRIPTION = "check_subscription"
CB_REFRESH_MY_REFERRALS = "refresh_my_referrals"
CB_SHOW_INVITE = "show_invite"
CB_SHOW_SHARE = "show_share"
CB_SHOW_MY_REFERRALS = "show_my_referrals"


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


def my_referrals_refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data=CB_REFRESH_MY_REFERRALS)]
        ]
    )


def welcome_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Taklif qilish", callback_data=CB_SHOW_INVITE),
                InlineKeyboardButton(text="📤 Ulashish", callback_data=CB_SHOW_SHARE),
            ],
            [InlineKeyboardButton(text="📊 Mening takliflarim", callback_data=CB_SHOW_MY_REFERRALS)],
        ]
    )
