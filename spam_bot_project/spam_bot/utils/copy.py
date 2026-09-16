HELP_TEXT = (
    "🛡️ <b>Spam Himoya Boti</b>\n\n"
    "Ushbu bot guruhingizni spam, ochiq-sochiq kontent va zararli havolalardan "
    "avtomatik himoya qiladi.\n\n"
    "<b>Buyruqlar:</b>\n"
    "/enable — guruh uchun himoyani yoqish (faqat guruh adminlari)\n"
    "/disable — himoyani o'chirish (faqat guruh adminlari)\n"
    "/setkey — sun'iy intellekt moderatsiyasi uchun shaxsiy Gemini kalitini saqlash\n"
    "/ban, /mute — javob berilgan foydalanuvchini moderatsiya qilish (reply orqali)\n"
    "/tokens — Gemini tokenlaridan foydalanish va xarajat hisoboti\n"
    "/stats — guruhlar va tutilgan spam statistikasi (operator uchun)\n"
    "/privacy — maxfiylik siyosati"
)

PRIVACY_TEXT = (
    "🔒 <b>Maxfiylik</b>\n\n"
    "Har bir guruhning Gemini API kaliti shifrlangan holda saqlanadi, umumiy "
    "kalit ishlatilmaydi. Profil rasmlari tekshiruvi butunlay mahalliy "
    "darajada (bulutga so'rov yubormasdan) amalga oshiriladi. Spam hisobot "
    "matnlari va foydalanish yozuvlari muayyan muddatdan keyin avtomatik "
    "tozalanadi."
)

ENABLE_SUCCESS = "✅ Himoya yoqildi. Bot endi spam, NSFW va zararli havolalarni kuzatadi."
DISABLE_SUCCESS = "🚫 Himoya o'chirildi."
GROUP_LIMIT_REACHED = "⚠️ Siz uchun ruxsat etilgan guruhlar soni chegarasiga yetdingiz."

SETKEY_PROMPT = "🔑 Gemini API kalitingizni shaxsiy xabarlar orqali saqlash uchun quyidagi havolaga o'ting (15 daqiqa amal qiladi):\n{link}"
SETKEY_DM_ONLY = "Bu buyruq faqat guruh ichida ishlaydi. Iltimos, guruhda /setkey deb yozing."
SETKEY_LINK_SENT_TO_DM = "📩 Kalitni saqlash havolasi sizga shaxsiy xabarlarda yuborildi."
SETKEY_CANNOT_DM = "❗️ Sizga shaxsiy xabar yubora olmadim. Avval botga /start bosing, so'ng qayta urinib ko'ring."

REPLY_REQUIRED = "Iltimos, moderatsiya qilinadigan foydalanuvchining xabariga javob (reply) qilib buyruq bering."

BAN_DONE = "🔨 {name} guruhdan bloklandi."
MUTE_DONE = "🔇 {name} 24 soatga ovozi o'chirildi."

UNBAN_BUTTON = "✅ Blokdan chiqarish"
UNMUTE_BUTTON = "🔊 Ovozini yoqish"
UNBAN_DONE = "✅ Blokdan chiqarildi."
UNMUTE_DONE = "🔊 Ovozi yoqildi."

SPAM_DETECTED_TEMPLATE = (
    "🛡️ Spam aniqlandi va o'chirildi.\n"
    "Foydalanuvchi: {mention}\n"
    "Sabab: {reason}\n"
    "Chora: {action}"
)

REASON_LABELS = {
    "keyword": "kalit so'z",
    "ai": "sun'iy intellekt (kontent moderatsiyasi)",
    "malware_link": "zararli/behayo havola",
    "nsfw_photo": "behayo profil rasmi",
    "raid": "muvofiqlashtirilgan spam hujumi",
}

ACTION_LABELS = {
    "delete": "o'chirish",
    "mute": "24 soatga ovozini o'chirish",
    "ban": "guruhdan bloklash",
}
