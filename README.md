# Telegram Referral Bot

Referral tizimi orqali yopiq Telegram kanaliga kirish imkonini beruvchi bot.

## Stack

- Python 3.12, Aiogram 3.x
- PostgreSQL + SQLAlchemy 2.0 (async) + Alembic
- Redis (FSM storage)
- APScheduler (fon vazifalar)
- Docker Compose

## Loyiha holati

Ishlab chiqish bosqichma-bosqich davom etmoqda. Hozircha tayyor:

- [x] Loyiha skeleti, Docker, config, DB modellari, Alembic
- [ ] Foydalanuvchi oqimi: /start, obuna tekshiruvi, asosiy menyu
- [ ] Referral yaratish, aniqlash va anti-fraud qoidalar
- [ ] Mening takliflarim / Maxfiy havolani olish + invite link hayot sikli
- [ ] Admin panel: welcome, kanallar, referral kontent, talablar
- [ ] Admin panel: broadcast, statistika, qidiruv, adminlar
- [ ] Xavfsizlik, logging, ishga tushirish yo'riqnomasi

## Lokal ishga tushirish

\`\`\`bash
cp .env.example .env
# .env faylida BOT_TOKEN va boshqa qiymatlarni to'ldiring

docker compose up -d --build
docker compose exec bot alembic upgrade head
\`\`\`
