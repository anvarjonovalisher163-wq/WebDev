from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.keyboards.admin import ADMIN_SETTINGS_BTN
from bot.models.channel import MandatoryChannel

CB_CHECK_SUBSCRIPTION = "check_subscription"
CB_REFRESH_MY_REFERRALS = "refresh_my_referrals"
CB_SHOW_INVITE = "show_invite"

BTN_MY_REFERRALS = "📊 Mening takliflarim"
BTN_LEADERBOARD = "🏆 Reyting"
BTN_MARRA = "📖 Marra"

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


CB_MARRA_JOIN = "marra_join"
CB_MARRA_LEAVE = "marra_leave"


def marra_keyboard(marra_url: str, is_participant: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📖 Marra sahifasini ochish", url=marra_url)
        ]
    ]
    if is_participant:
        rows.append([InlineKeyboardButton(text="🚫 Marradan chiqish", callback_data=CB_MARRA_LEAVE)])
    else:
        rows.append([InlineKeyboardButton(text="✅ Marraga qo'shilaman", callback_data=CB_MARRA_JOIN)])
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


def main_reply_keyboard(
    webapp_url: str = "", is_admin: bool = False, marra_enabled: bool = False
) -> Optional[ReplyKeyboardMarkup]:
    """Doimiy pastki menyu. Mini App manzili sozlangan bo'lsa, "Mening
    takliflarim" va "Reyting" uchun alohida tugma kerak emas - ikkalasi ham
    xabar yozish maydoni yonidagi tabiiy Telegram menyu tugmasi ("Reyting")
    orqali ochiladigan yagona Mini App ichidagi tablarga aylantirilgan.
    Shu holatda oddiy foydalanuvchi uchun pastki menyuda ko'rsatiladigan
    hech narsa qolmaydi (None qaytadi). Mini App sozlanmagan bo'lsa,
    ikkalasi ham matnli (eski) tugmalar sifatida ko'rsatiladi. Adminlar
    uchun har doim qo'shimcha "Sozlamalar" tugmasi qo'shiladi. "Marra"
    havolasi sozlangan bo'lsa, alohida tugma qo'shiladi."""
    rows = []
    if not webapp_url:
        rows.append([KeyboardButton(text=BTN_MY_REFERRALS), KeyboardButton(text=BTN_LEADERBOARD)])
    if marra_enabled:
        rows.append([KeyboardButton(text=BTN_MARRA)])
    if is_admin:
        rows.append([KeyboardButton(text=ADMIN_SETTINGS_BTN)])

    if not rows:
        return None
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
