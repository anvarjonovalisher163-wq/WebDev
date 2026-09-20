from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.models.admin import Admin
from bot.models.channel import MandatoryChannel
from bot.models.user import User

ADMIN_SETTINGS_BTN = "⚙️ Sozlamalar"

CB_ADMIN_WELCOME = "admin:welcome"
CB_ADMIN_WELCOME_TEXT = "admin:welcome_text"
CB_ADMIN_WELCOME_MEDIA = "admin:welcome_media"
CB_ADMIN_WELCOME_MEDIA_REMOVE = "admin:welcome_media_remove"

CB_ADMIN_CHANNELS = "admin:channels"
CB_ADMIN_CHANNEL_ADD = "admin:channel_add"
CB_ADMIN_CHANNELS_TEXT = "admin:channels_text"

CB_ADMIN_REFERRAL_TEXT = "admin:referral_text"
CB_ADMIN_REFERRAL_IMAGE = "admin:referral_image"
CB_ADMIN_REFERRAL_PREVIEW = "admin:referral_preview"
CB_ADMIN_REFERRAL_IMAGE_REMOVE = "admin:referral_image_remove"
CB_ADMIN_SHARE_TEXT = "admin:share_text"

CB_ADMIN_REQUIREMENTS = "admin:requirements"

CB_ADMIN_SECRET_CHANNEL = "admin:secret_channel"
CB_ADMIN_SECRET_SET_CHANNEL = "admin:secret_set_channel"
CB_ADMIN_SECRET_SET_TTL = "admin:secret_set_ttl"
CB_ADMIN_SECRET_SET_LIMIT = "admin:secret_set_limit"
CB_ADMIN_SECRET_TOGGLE_REISSUE = "admin:secret_toggle_reissue"
CB_ADMIN_SECRET_SET_MAX_REISSUE = "admin:secret_set_max_reissue"

CB_ADMIN_BROADCAST = "admin:broadcast"
CB_ADMIN_BROADCAST_CONFIRM = "admin:broadcast_confirm"

CB_ADMIN_STATS = "admin:stats"
CB_ADMIN_STATS_CSV = "admin:stats_csv"

CB_ADMIN_SEARCH = "admin:search"

CB_ADMIN_ADMINS = "admin:admins"
CB_ADMIN_ADMIN_ADD = "admin:admin_add"

CB_ADMIN_SEASONS = "admin:seasons"
CB_ADMIN_SEASON_END_PROMPT = "admin:season_end_prompt"
CB_ADMIN_SEASON_END_CONFIRM = "admin:season_end_confirm"

CB_ADMIN_CERTIFICATES = "admin:certificates"
CB_ADMIN_CERT_ISSUE_PROMPT = "admin:cert_issue_prompt"
CB_ADMIN_CERT_ISSUE_CONFIRM = "admin:cert_issue_confirm"

CB_ADMIN_BACK = "admin:back"
CB_ADMIN_CANCEL = "admin:cancel"


def admin_main_menu_keyboard(webapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📝 Welcome xabari", callback_data=CB_ADMIN_WELCOME)],
        [InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data=CB_ADMIN_CHANNELS)],
        [
            InlineKeyboardButton(text="🖼 Referral rasmi", callback_data=CB_ADMIN_REFERRAL_IMAGE),
            InlineKeyboardButton(text="✍️ Referral matni", callback_data=CB_ADMIN_REFERRAL_TEXT),
        ],
        [InlineKeyboardButton(text="📤 Ulashish matni", callback_data=CB_ADMIN_SHARE_TEXT)],
        [InlineKeyboardButton(text="🔢 Talablar soni", callback_data=CB_ADMIN_REQUIREMENTS)],
        [InlineKeyboardButton(text="🔐 Maxfiy kanal sozlamalari", callback_data=CB_ADMIN_SECRET_CHANNEL)],
        [InlineKeyboardButton(text="🏆 Mavsumlar", callback_data=CB_ADMIN_SEASONS)],
        [InlineKeyboardButton(text="🎓 Sertifikatlar", callback_data=CB_ADMIN_CERTIFICATES)],
    ]
    if webapp_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🖥 Sertifikat dizayneri (Web App)",
                    web_app=WebAppInfo(url=f"{webapp_url}/admin"),
                )
            ]
        )
    rows += [
        [InlineKeyboardButton(text="📤 E'lon yuborish", callback_data=CB_ADMIN_BROADCAST)],
        [InlineKeyboardButton(text="📊 Statistika", callback_data=CB_ADMIN_STATS)],
        [InlineKeyboardButton(text="🔍 Foydalanuvchini qidirish", callback_data=CB_ADMIN_SEARCH)],
        [InlineKeyboardButton(text="👥 Adminlar", callback_data=CB_ADMIN_ADMINS)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)]]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_ADMIN_CANCEL)]]
    )


def welcome_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Matnni o'zgartirish", callback_data=CB_ADMIN_WELCOME_TEXT)],
            [InlineKeyboardButton(text="🖼 Media biriktirish", callback_data=CB_ADMIN_WELCOME_MEDIA)],
            [InlineKeyboardButton(text="🗑 Mediani o'chirish", callback_data=CB_ADMIN_WELCOME_MEDIA_REMOVE)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def referral_content_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Matnni o'zgartirish", callback_data=CB_ADMIN_REFERRAL_TEXT)],
            [InlineKeyboardButton(text="🖼 Rasmni o'zgartirish", callback_data=CB_ADMIN_REFERRAL_IMAGE)],
            [InlineKeyboardButton(text="🗑 Rasmni o'chirish", callback_data=CB_ADMIN_REFERRAL_IMAGE_REMOVE)],
            [InlineKeyboardButton(text="👁 Oldindan ko'rish", callback_data=CB_ADMIN_REFERRAL_PREVIEW)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def channels_list_keyboard(channels: list[MandatoryChannel]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        status = "✅" if channel.is_active else "⛔"
        rows.append(
            [InlineKeyboardButton(text=f"{status} {channel.title}", callback_data=f"admin:channel:{channel.id}")]
        )
    rows.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data=CB_ADMIN_CHANNEL_ADD)])
    rows.append([InlineKeyboardButton(text="✍️ Obuna so'rovi matni", callback_data=CB_ADMIN_CHANNELS_TEXT)])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_detail_keyboard(channel: MandatoryChannel) -> InlineKeyboardMarkup:
    toggle_text = "⛔ Faolsizlantirish" if channel.is_active else "✅ Faollashtirish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin:channel_toggle:{channel.id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"admin:channel_del:{channel.id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_CHANNELS)],
        ]
    )


def secret_channel_menu_keyboard(reissue_allowed: bool) -> InlineKeyboardMarkup:
    reissue_text = (
        "🔄 Qayta olish: yoqilgan (o'chirish)" if reissue_allowed else "🔄 Qayta olish: o'chirilgan (yoqish)"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Kanalni sozlash", callback_data=CB_ADMIN_SECRET_SET_CHANNEL)],
            [InlineKeyboardButton(text="⏱ Amal qilish muddati", callback_data=CB_ADMIN_SECRET_SET_TTL)],
            [InlineKeyboardButton(text="🔢 Foydalanish limiti", callback_data=CB_ADMIN_SECRET_SET_LIMIT)],
            [InlineKeyboardButton(text=reissue_text, callback_data=CB_ADMIN_SECRET_TOGGLE_REISSUE)],
            [InlineKeyboardButton(text="🔁 Maksimal qayta urinish", callback_data=CB_ADMIN_SECRET_SET_MAX_REISSUE)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yuborish", callback_data=CB_ADMIN_BROADCAST_CONFIRM)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_ADMIN_CANCEL)],
        ]
    )


def stats_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 CSV yuklab olish", callback_data=CB_ADMIN_STATS_CSV)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def search_results_keyboard(users: list[User]) -> InlineKeyboardMarkup:
    rows = []
    for user in users:
        label = f"👤 {user.first_name} (@{user.username})" if user.username else f"👤 {user.first_name} [{user.tg_id}]"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"admin:user:{user.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_detail_keyboard(user: User) -> InlineKeyboardMarkup:
    block_text = "✅ Blokdan chiqarish" if user.is_blocked else "🚫 Bloklash"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=block_text, callback_data=f"admin:user_toggle_block:{user.id}")],
            [InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data=f"admin:user_message:{user.id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_SEARCH)],
        ]
    )


def seasons_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Yangi mavsum boshlash", callback_data=CB_ADMIN_SEASON_END_PROMPT)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)],
        ]
    )


def season_end_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha, yakunlash", callback_data=CB_ADMIN_SEASON_END_CONFIRM)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_ADMIN_SEASONS)],
        ]
    )


def certificates_menu_keyboard(ready_count: int) -> InlineKeyboardMarkup:
    rows = []
    if ready_count > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🎓 Sertifikatlarni berish ({ready_count})",
                    callback_data=CB_ADMIN_CERT_ISSUE_PROMPT,
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def certificates_issue_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha, yuborish", callback_data=CB_ADMIN_CERT_ISSUE_CONFIRM)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_ADMIN_CERTIFICATES)],
        ]
    )


def admins_list_keyboard(admins: list[Admin], can_manage: bool) -> InlineKeyboardMarkup:
    rows = []
    for admin in admins:
        label = f"{'👑 ' if admin.is_super_admin else '🛡 '}{admin.tg_id}"
        row = [InlineKeyboardButton(text=label, callback_data=f"admin:noop:{admin.id}")]
        if can_manage and not admin.is_super_admin:
            row.append(
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"admin:admin_del:{admin.id}")
            )
        rows.append(row)
    if can_manage:
        rows.append([InlineKeyboardButton(text="➕ Admin qo'shish", callback_data=CB_ADMIN_ADMIN_ADD)])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_ADMIN_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
