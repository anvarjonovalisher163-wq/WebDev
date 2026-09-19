from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.keyboards.admin import ADMIN_SETTINGS_BTN
from bot.models.channel import MandatoryChannel

CB_CHECK_SUBSCRIPTION = "check_subscription"
CB_REFRESH_MY_REFERRALS = "refresh_my_referrals"
CB_SHOW_INVITE = "show_invite"

BTN_MY_REFERRALS = "📊 Mening takliflarim"
BTN_LEADERBOARD = "🏆 Reyting"

DEFAULT_SHARE_TEXT = "Yopiq kanalga qo'shilish uchun shu botga kiring!"


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


def welcome_actions_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔗 Taklif qilish", callback_data=CB_SHOW_INVITE)]]
    )


def main_reply_keyboard(webapp_url: str = "", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Doimiy pastki menyu: "Mening takliflarim" va "Reyting" (agar Mini App
    manzili sozlangan bo'lsa, Reyting to'g'ridan-to'g'ri uni ochadi), adminlar
    uchun qo'shimcha "Sozlamalar" tugmasi bilan."""
    leaderboard_button = (
        KeyboardButton(text=BTN_LEADERBOARD, web_app=WebAppInfo(url=webapp_url))
        if webapp_url
        else KeyboardButton(text=BTN_LEADERBOARD)
    )
    rows = [[KeyboardButton(text=BTN_MY_REFERRALS), leaderboard_button]]
    if is_admin:
        rows.append([KeyboardButton(text=ADMIN_SETTINGS_BTN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
