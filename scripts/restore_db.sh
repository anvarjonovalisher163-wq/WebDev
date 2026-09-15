#!/usr/bin/env bash
set -euo pipefail

# Zaxira nusxadan bazani tiklash skripti.
# Foydalanish: ./scripts/restore_db.sh backups/referral_bot_20250101_120000.sql.gz

if [ $# -ne 1 ]; then
  echo "Foydalanish: $0 <backup_fayli.sql.gz>"
  exit 1
fi

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

gunzip -c "$1" | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"

echo "Baza tiklandi: $1"
