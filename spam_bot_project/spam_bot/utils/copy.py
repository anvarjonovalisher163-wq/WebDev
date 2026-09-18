START_TEXT = (
    "👋 Salom! Men — guruhlarni spam, ochiq-sochiq kontent va zararli "
    "havolalardan avtomatik himoya qiluvchi botman.\n\n"
    "Meni guruhingizga admin qilib qo'shing va u yerda /enable buyrug'ini "
    "bering — himoya darhol ishga tushadi.\n\n"
    "Barcha buyruqlar ro'yxati uchun /help ni bosing."
)

HELP_TEXT = (
    "🛡️ <b>Spam Himoya Boti</b>\n\n"
    "Ushbu bot guruhingizni spam, ochiq-sochiq kontent va zararli havolalardan "
    "avtomatik himoya qiladi.\n\n"
    "<b>Buyruqlar:</b>\n"
    "/enable — guruh uchun himoyani yoqish (faqat guruh adminlari)\n"
    "/disable — himoyani o'chirish (faqat guruh adminlari)\n"
    "/obuna — Telegram Stars orqali obunani to'lash/uzaytirish\n"
    "/setkey — sun'iy intellekt moderatsiyasi uchun shaxsiy Gemini kalitini saqlash\n"
    "/ban, /mute — javob berilgan foydalanuvchini moderatsiya qilish (reply orqali)\n"
    "/tokens — Gemini tokenlaridan foydalanish va xarajat hisoboti\n"
    "/stats — guruhlar va tutilgan spam statistikasi (operator uchun)\n"
    "/daromad — Stars daromadi hisoboti (operator uchun)\n"
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
ENABLE_TRIAL_STARTED = (
    "✅ Himoya yoqildi! Sizga {days} kunlik bepul sinov muddati berildi.\n"
    "Muddat tugagach, davom etish uchun /obuna buyrug'i orqali Telegram Stars bilan to'lov qilishingiz kerak bo'ladi."
)
ENABLE_EXPIRED_NOTICE = (
    "⏰ Bepul sinov muddati yoki obunangiz tugagan, shuning uchun himoya vaqtincha to'xtatilgan.\n"
    "Davom ettirish uchun guruhda /obuna buyrug'ini bering."
)
DISABLE_SUCCESS = "🚫 Himoya o'chirildi."
GROUP_LIMIT_REACHED = "⚠️ Siz uchun ruxsat etilgan guruhlar soni chegarasiga yetdingiz."

SUBSCRIPTION_INVOICE_TITLE = "Spam Himoya Boti — obuna"
SUBSCRIPTION_INVOICE_DESCRIPTION = "\"{group}\" guruhi uchun {days} kunlik himoya obunasi."
SUBSCRIPTION_LABEL = "Obuna ({days} kun)"
SUBSCRIPTION_GROUP_ONLY = "Bu buyruq faqat guruh ichida ishlaydi. Iltimos, guruhda /obuna deb yozing."
SUBSCRIPTION_PAID_GROUP = "✅ To'lov qabul qilindi! Himoya {until} sanasigacha faol."
SUBSCRIPTION_PAID_DM = "✅ Rahmat! \"{group}\" guruhi uchun to'lovingiz qabul qilindi, himoya {until} sanasigacha faol."

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

OPERATOR_NOTICE_TEMPLATE = (
    "🛡️ <b>{group}</b> guruhida chora ko'rildi\n"
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
