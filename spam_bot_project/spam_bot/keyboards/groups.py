from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from spam_bot.models.group import Group

CB_GROUPS_BACK = "groups:back"


def groups_list_keyboard(groups: list[Group]) -> InlineKeyboardMarkup:
    rows = []
    for group in groups:
        emoji = "✅" if group.enabled else "⛔"
        title = group.title or str(group.chat_id)
        rows.append(
            [InlineKeyboardButton(text=f"{emoji} {title}", callback_data=f"group:{group.chat_id}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def group_detail_keyboard(group: Group) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♾️ Cheksiz bepul qilish", callback_data=f"group_free:{group.chat_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Obunani +30 kun uzaytirish (qo'lda)",
                    callback_data=f"group_extend:{group.chat_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Himoyani o'chirish", callback_data=f"group_disable:{group.chat_id}"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data=CB_GROUPS_BACK)],
        ]
    )
