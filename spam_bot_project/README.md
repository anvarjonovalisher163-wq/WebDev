# Spam Himoya Boti (Telegram)

Guruhlarni spam, ochiq-sochiq kontent va zararli havolalardan avtomatik
himoya qiluvchi, ko'p guruhli (multi-tenant), o'z-o'ziga xizmat ko'rsatuvchi
Telegram boti. Har kim botni o'z guruhiga qo'shib, `/enable` buyrug'i bilan
himoyani yoqishi mumkin.

Bu loyiha ushbu repodagi referral botdan mustaqil, alohida bot sifatida
ishlaydi (o'z Docker, baza va konfiguratsiyasi bilan).

## Xususiyatlari

- **Kalit so'z/regex qatlami** — standart pattern ro'yxati (`patterns/seed_patterns.txt`)
  va har bir guruh uchun admin qo'shgan qo'shimcha kalit so'zlar.
- **AI (Gemini) moderatsiyasi, BYOK** — `/setkey` orqali har bir guruh o'z
  shaxsiy Gemini API kalitini shifrlangan holda saqlaydi; shubhali xabarlar
  ochiq-sochiq kontent/flirt-spam uchun tekshiriladi.
- **NSFW profil rasm skaneri** — yangi a'zolar va birinchi xabar yozganlarning
  profil rasmi mahalliy darajada (bulutsiz, ixtiyoriy `nudenet` kutubxonasi
  orqali) tekshiriladi.
- **Zararli havola aniqlash** — `.apk`/`.exe` kabi yuklab olinadigan fayllar
  va ochiq-sochiq kanal havolalari kalit so'z tekshiruvidan oldin bloklanadi.
- **Ommaviy hujum (raid) detektori** — qisqa vaqt ichida bir nechta
  akkountdan kelgan bir xil xabarlarni aniqlab, barchasini birdaniga
  jazolaydi.
- **Admin asboblari** — `/ban`, `/mute` (reply orqali), ogohlantirish
  xabaridagi Blokdan chiqarish/Ovozini yoqish tugmalari.
- **Hisobot** — `/tokens` (Gemini xarajati), `/stats` (operator uchun,
  shaxsiy xabarda), operatorga kunlik hisobot.

## Qanday ishlaydi

Har bir xabar quyidagi zanjirdan o'tadi, birinchi mos kelgan qoida ishga tushadi:

1. Profil skaneri (a'zo bo'lganda va birinchi xabarda, bir marta)
2. Zararli/behayo havola tekshiruvi
3. Kalit so'z qatlami (bepul)
4. AI qatlami (agar guruh Gemini kaliti bo'lsa)
5. Ommaviy hujum detektori

Aniqlangan xabar o'chiriladi; jiddiy holatlarda (zararli havola, aniq NSFW,
AI "adult" tasnifi) foydalanuvchi bloklanadi, boshqa hollarda 24 soatga
ovozi o'chiriladi va admin ogohlantirish tugmalari orqali qarorni bekor
qilishi mumkin.

## Texnologiyalar

Python 3.12 · aiogram 3 · SQLAlchemy 2 (async) + PostgreSQL · Google Gemini
(REST, BYOK) · aiohttp (`/setkey` shakli uchun) · APScheduler · ixtiyoriy
NudeNet (NSFW).

## O'rnatish

```bash
cd spam_bot_project
cp .env.example .env
# .env faylida BOT_TOKEN, ADMIN_TELEGRAM_IDS, KEY_ENCRYPTION_SECRET, BASE_URL'ni to'ldiring

docker compose up -d --build
```

Baza jadvallari bot birinchi marta ishga tushganda avtomatik yaratiladi.

### Telefondan joylashtirish (kompyutersiz)

Docker/terminal shart emas — [Railway](https://railway.app) yoki
[Render](https://render.com) kabi platformalarga brauzer orqali joylashtirish
mumkin:

1. Railway'da **New Project → Deploy from GitHub repo** → ushbu repo, "Root
   Directory" sifatida `spam_bot_project`ni ko'rsating (Railway `Dockerfile`ni
   avtomatik topib quradi).
2. **+ New → Database → PostgreSQL** qo'shing.
3. Bot xizmatining **Variables** bo'limida quyidagilarni kiriting:
   - `BOT_TOKEN`, `ADMIN_TELEGRAM_IDS`, `KEY_ENCRYPTION_SECRET`
   - `DATABASE_URL` — Railway Postgres'ning o'zi taklif qiladigan
     `${{Postgres.DATABASE_URL}}` referensini tanlang (POSTGRES_* alohida
     kerak emas)
   - `BASE_URL` — Railway avtomatik bergan ommaviy domenni (`https://...up.railway.app`)
     "Settings → Networking → Generate Domain" orqali oling va shu yerga qo'ying
4. Deploy tugmasini bosing — bot avtomatik quriladi va ishga tushadi.

### NSFW profil rasm skaneri (ixtiyoriy)

```bash
pip install -r requirements-nsfw.txt
```

O'rnatilmasa, bot xatosiz ishlashda davom etadi — faqat NSFW rasm tekshiruvi
o'chirilgan bo'ladi.

### Botga kerakli Telegram huquqlari

Botni guruhga qo'shib, **Xabarlarni o'chirish** va **Foydalanuvchilarni
bloklash/cheklash** huquqlariga ega admin qiling, so'ng guruhda `/enable`
buyrug'ini bering. `/setkey` uchun BotFather'da maxfiylik rejimini
o'chirish shart emas — bot allaqachon barcha xabarlarni ko'rish huquqiga ega
bo'lishi kerak (`/setprivacy` → Disable), aks holda oddiy a'zo xabarlarini
o'qiy olmaydi.

## Buyruqlar

| Buyruq | Kim uchun | Vazifasi |
|---|---|---|
| `/enable` · `/disable` | Guruh adminlari | Himoyani yoqish/o'chirish |
| `/setkey` | Guruh adminlari | Gemini kalitini saqlash (shaxsiy, bir martalik havola) |
| `/ban` · `/mute` | Guruh adminlari | Javob berilgan foydalanuvchini moderatsiya qilish |
| `/tokens` | Guruh adminlari | Gemini tokenlaridan foydalanish + xarajat |
| `/stats` | Operator (shaxsiy xabar) | Guruhlar va spam statistikasi |
| `/help` · `/privacy` | Hamma | Qo'llanma / maxfiylik siyosati |

## Litsenziya haqida eslatma

Ushbu loyiha [anvarnarz/killspam-bot](https://github.com/anvarnarz/killspam-bot)
g'oyasidan ilhomlanib, kodni nusxalamagan holda mustaqil yozilgan (u
PolyForm Noncommercial litsenziyasi ostida tarqatiladi).
