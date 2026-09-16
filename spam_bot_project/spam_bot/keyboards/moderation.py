from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from spam_bot.utils.copy import UNBAN_BUTTON, UNMUTE_BUTTON


def unban_keyboard(chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=UNBAN_BUTTON, callback_data=f"unban:{chat_id}:{user_id}")]]
    )


def unmute_keyboard(chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=UNMUTE_BUTTON, callback_data=f"unmute:{chat_id}:{user_id}")]]
    )
