#!/usr/bin/env bash
set -euo pipefail

# Referral bot PostgreSQL bazasini zaxiralash skripti.
# Foydalanish: ./scripts/backup_db.sh
# docker-compose orqali ishga tushirilgan "postgres" servisidan .sql.gz fayl yaratadi.

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_FILE="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT_FILE"

echo "Zaxira nusxa yaratildi: $OUT_FILE"

# 30 kundan eski zaxiralarni avtomatik o'chirish
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
