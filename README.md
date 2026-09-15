# Telegram Referral Bot

Referral tizimi orqali yopiq Telegram kanaliga kirish imkonini beruvchi bot.
Foydalanuvchi botga referral havolasi orqali do'stlarini taklif qiladi;
belgilangan miqdorda tasdiqlangan taklif to'planganda bot yopiq kanalga
qo'shilish uchun bir martalik, muddatli taklif havolasi beradi.

## Stack

- Python 3.12, Aiogram 3.x (long polling)
- PostgreSQL + SQLAlchemy 2.0 (async) + Alembic
- Redis (FSM holatlarini saqlash uchun)
- APScheduler (muddati o'tgan havolalarni avtomatik yopish)
- Docker Compose

## Loyiha holati

- [x] Loyiha skeleti, Docker, config, DB modellari, Alembic
- [x] Foydalanuvchi oqimi: /start, obuna tekshiruvi, asosiy menyu
- [x] Referral yaratish, aniqlash va anti-fraud qoidalar
- [x] Mening takliflarim / Maxfiy havolani olish + invite link hayot sikli
- [x] Admin panel: welcome, kanallar, referral kontent, talablar
- [x] Admin panel: broadcast, statistika, qidiruv, adminlar
- [x] Xavfsizlik, logging, ishga tushirish yo'riqnomasi

## Ishga tushirish

```bash
cp .env.example .env
# .env faylida BOT_TOKEN, SUPER_ADMIN_IDS va boshqa qiymatlarni to'ldiring

docker compose up -d --build
docker compose exec bot alembic upgrade head
```

`SUPER_ADMIN_IDS` da ko'rsatilgan Telegram ID'lar bot birinchi marta
ishga tushganda avtomatik ravishda bosh administrator sifatida bazaga
qo'shiladi (`/admin` buyrug'i orqali admin panelga kirish imkoniyati
paydo bo'ladi).

## Muhit o'zgaruvchilari (.env)

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | BotFather'dan olingan bot tokeni |
| `SUPER_ADMIN_IDS` | Vergul bilan ajratilgan bosh admin Telegram ID'lari |
| `POSTGRES_*` | PostgreSQL ulanish ma'lumotlari |
| `REDIS_*` | Redis ulanish ma'lumotlari (FSM storage) |
| `LOG_LEVEL` | Konsol logging darajasi (masalan, `INFO`) |

## Botga kerakli Telegram huquqlari

- **Majburiy kanallar**: bot administrator etib qo'shilishi kerak (a'zolikni
  tekshirish uchun).
- **Yopiq (maxfiy) kanal**: bot administrator etib qo'shilishi va
  "foydalanuvchilarni taklif qilish" (invite users) huquqiga ega bo'lishi
  kerak (bir martalik taklif havolalarini yaratish/bekor qilish uchun).

Kanallarni admin paneldan ("Majburiy kanallar" / "Maxfiy kanal sozlamalari")
qo'shishdan oldin botni tegishli kanalga administrator qilib qo'shing.

## Admin panelidan foydalanish

Bosh admin yoki qo'shilgan admin `/admin` buyrug'ini yuboradi va quyidagi
bo'limlarga ega bo'ladi:

- **Welcome xabari** — matn (HTML formatlash bilan) va rasm/video
- **Majburiy kanallar** — qo'shish, faollashtirish/faolsizlantirish, o'chirish
- **Referral rasmi / matni** — `{referral_link}` o'zgaruvchisi bilan
- **Talablar soni** — yopiq kanal uchun zarur tasdiqlangan referral soni
- **Maxfiy kanal sozlamalari** — kanal, havola muddati, foydalanish limiti,
  qayta havola olish siyosati
- **E'lon yuborish** — barcha foydalanuvchilarga ommaviy xabar (oldindan
  ko'rish va tasdiqlash bilan)
- **Statistika** — umumiy/referral statistikasi, konversiya voronkasi,
  top-10 taklif qiluvchi, CSV eksport
- **Foydalanuvchini qidirish** — ID/username/ism bo'yicha, bloklash va
  individual xabar yuborish
- **Adminlar** — yangi admin qo'shish/o'chirish (faqat bosh admin)

Oddiy foydalanuvchilar uchun `/admin` buyrug'i hech qanday ta'sir
ko'rsatmaydi.

## Ma'lumotlar bazasini zaxiralash va tiklash

```bash
./scripts/backup_db.sh                              # backups/ papkasiga .sql.gz yaratadi
./scripts/restore_db.sh backups/<fayl_nomi>.sql.gz   # zaxiradan tiklaydi
```

Zaxira skriptini kunlik `cron` orqali ishga tushirish tavsiya etiladi:

```
0 3 * * * /path/to/project/scripts/backup_db.sh >> /var/log/referral_bot_backup.log 2>&1
```

## Loyiha tuzilmasi

```
bot/
├── handlers/       # aiogram routerlari (user/, admin/)
├── services/       # biznes mantiq (referral, invite, subscription, stats, broadcast)
├── repositories/   # SQLAlchemy so'rovlari
├── models/         # ORM modellari
├── keyboards/      # inline klaviaturalar
├── states/         # FSM holatlari (admin oqimlari uchun)
├── middlewares/     # DB session middleware
├── filters/        # IsAdmin / IsSuperAdmin
├── jobs/           # APScheduler fon vazifalari
└── main.py         # kirish nuqtasi

alembic/            # DB migratsiyalari
scripts/            # backup/restore skriptlari
```

## Xavfsizlik

- Admin panel faqat `admins` jadvalidagi (yoki `.env` orqali seed qilingan)
  Telegram ID'lar uchun ochiladi.
- Har bir admin amali `admin_logs` jadvaliga yoziladi.
- Referral anti-fraud qoidalari (`bot/services/referral_service.py`):
  o'z-o'ziga referral, bloklangan referrer va qayta ro'yxatdan
  o'tishlar hisobga olinmaydi.
- Maxfiy kanal havolasi faqat barcha shartlar bajarilgandan keyin
  yaratiladi, bir marta ishlaydi va muddati tugagach avtomatik bekor
  qilinadi (APScheduler orqali har daqiqada tekshiriladi).
- Barcha ishlov berilmagan xatolar markazlashtirilgan error handler
  orqali `logs/bot.log` fayliga yoziladi (`bot/utils/error_handler.py`).
- Bot tokeni va DB parollari faqat `.env` faylida saqlanadi (`.gitignore`
  orqali repozitoriyaga tushishi oldini olingan).
