from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models.channel import MandatoryChannel

CB_ADMIN_WELCOME = "admin:welcome"
CB_ADMIN_WELCOME_TEXT = "admin:welcome_text"
CB_ADMIN_WELCOME_MEDIA = "admin:welcome_media"
CB_ADMIN_WELCOME_MEDIA_REMOVE = "admin:welcome_media_remove"

CB_ADMIN_CHANNELS = "admin:channels"
CB_ADMIN_CHANNEL_ADD = "admin:channel_add"

CB_ADMIN_REFERRAL_TEXT = "admin:referral_text"
CB_ADMIN_REFERRAL_IMAGE = "admin:referral_image"
CB_ADMIN_REFERRAL_PREVIEW = "admin:referral_preview"
CB_ADMIN_REFERRAL_IMAGE_REMOVE = "admin:referral_image_remove"

CB_ADMIN_REQUIREMENTS = "admin:requirements"

CB_ADMIN_SECRET_CHANNEL = "admin:secret_channel"
CB_ADMIN_SECRET_SET_CHANNEL = "admin:secret_set_channel"
CB_ADMIN_SECRET_SET_TTL = "admin:secret_set_ttl"
CB_ADMIN_SECRET_SET_LIMIT = "admin:secret_set_limit"
CB_ADMIN_SECRET_TOGGLE_REISSUE = "admin:secret_toggle_reissue"
CB_ADMIN_SECRET_SET_MAX_REISSUE = "admin:secret_set_max_reissue"

CB_ADMIN_BROADCAST = "admin:broadcast"
CB_ADMIN_STATS = "admin:stats"
CB_ADMIN_SEARCH = "admin:search"
CB_ADMIN_ADMINS = "admin:admins"

CB_ADMIN_BACK = "admin:back"
CB_ADMIN_CANCEL = "admin:cancel"


def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Welcome xabari", callback_data=CB_ADMIN_WELCOME)],
            [InlineKeyboardButton(text="Majburiy kanallar", callback_data=CB_ADMIN_CHANNELS)],
            [
                InlineKeyboardButton(text="Referral rasmi", callback_data=CB_ADMIN_REFERRAL_IMAGE),
                InlineKeyboardButton(text="Referral matni", callback_data=CB_ADMIN_REFERRAL_TEXT),
            ],
            [InlineKeyboardButton(text="Talablar soni", callback_data=CB_ADMIN_REQUIREMENTS)],
            [InlineKeyboardButton(text="Maxfiy kanal sozlamalari", callback_data=CB_ADMIN_SECRET_CHANNEL)],
            [InlineKeyboardButton(text="E'lon yuborish", callback_data=CB_ADMIN_BROADCAST)],
            [InlineKeyboardButton(text="Statistika", callback_data=CB_ADMIN_STATS)],
            [InlineKeyboardButton(text="Foydalanuvchini qidirish", callback_data=CB_ADMIN_SEARCH)],
            [InlineKeyboardButton(text="Adminlar", callback_data=CB_ADMIN_ADMINS)],
        ]
    )


def back_to_admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Orqaga", callback_data=CB_ADMIN_BACK)]]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data=CB_ADMIN_CANCEL)]]
    )


def welcome_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Matnni o'zgartirish", callback_data=CB_ADMIN_WELCOME_TEXT)],
            [InlineKeyboardButton(text="Media biriktirish", callback_data=CB_ADMIN_WELCOME_MEDIA)],
            [InlineKeyboardButton(text="Mediani o'chirish", callback_data=CB_ADMIN_WELCOME_MEDIA_REMOVE)],
            [InlineKeyboardButton(text="Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def referral_content_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Matnni o'zgartirish", callback_data=CB_ADMIN_REFERRAL_TEXT)],
            [InlineKeyboardButton(text="Rasmni o'zgartirish", callback_data=CB_ADMIN_REFERRAL_IMAGE)],
            [InlineKeyboardButton(text="Rasmni o'chirish", callback_data=CB_ADMIN_REFERRAL_IMAGE_REMOVE)],
            [InlineKeyboardButton(text="Oldindan ko'rish", callback_data=CB_ADMIN_REFERRAL_PREVIEW)],
            [InlineKeyboardButton(text="Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def channels_list_keyboard(channels: list[MandatoryChannel]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        status = "✅" if channel.is_active else "⛔"
        rows.append(
            [InlineKeyboardButton(text=f"{status} {channel.title}", callback_data=f"admin:channel:{channel.id}")]
        )
    rows.append([InlineKeyboardButton(text="+ Kanal qo'shish", callback_data=CB_ADMIN_CHANNEL_ADD)])
    rows.append([InlineKeyboardButton(text="Orqaga", callback_data=CB_ADMIN_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_detail_keyboard(channel: MandatoryChannel) -> InlineKeyboardMarkup:
    toggle_text = "Faolsizlantirish" if channel.is_active else "Faollashtirish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin:channel_toggle:{channel.id}")],
            [InlineKeyboardButton(text="O'chirish", callback_data=f"admin:channel_del:{channel.id}")],
            [InlineKeyboardButton(text="Orqaga", callback_data=CB_ADMIN_CHANNELS)],
        ]
    )


def secret_channel_menu_keyboard(reissue_allowed: bool) -> InlineKeyboardMarkup:
    reissue_text = "Qayta olish: yoqilgan (o'chirish)" if reissue_allowed else "Qayta olish: o'chirilgan (yoqish)"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Kanalni sozlash", callback_data=CB_ADMIN_SECRET_SET_CHANNEL)],
            [InlineKeyboardButton(text="Amal qilish muddati", callback_data=CB_ADMIN_SECRET_SET_TTL)],
            [InlineKeyboardButton(text="Foydalanish limiti", callback_data=CB_ADMIN_SECRET_SET_LIMIT)],
            [InlineKeyboardButton(text=reissue_text, callback_data=CB_ADMIN_SECRET_TOGGLE_REISSUE)],
            [InlineKeyboardButton(text="Maksimal qayta urinish", callback_data=CB_ADMIN_SECRET_SET_MAX_REISSUE)],
            [InlineKeyboardButton(text="Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )
