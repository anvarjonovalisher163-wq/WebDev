import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bot.config import settings
from bot.db.session import async_session_factory
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.referral_service import ReferralService
from bot.services.season_service import SeasonService
from bot.services.subscription_service import SubscriptionService

INIT_DATA_MAX_AGE_SECONDS = 86400
TELEGRAM_API = f"https://api.telegram.org/bot{settings.bot_token}"
TELEGRAM_FILE_URL = f"https://api.telegram.org/file/bot{settings.bot_token}"

STATIC_DIR = Path(__file__).parent / "static"
AVATAR_CACHE_DIR = STATIC_DIR / "avatars"
AVATAR_CACHE_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Reyting Mini App")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _verify_init_data(init_data: str) -> Optional[dict]:
    """Telegram WebApp initData'ni tekshiradi (rasmiy HMAC algoritmi bo'yicha)
    va ichidagi foydalanuvchi ma'lumotini qaytaradi. Noto'g'ri/eskirgan bo'lsa None."""
    if not init_data:
        return None

    pairs = dict(parse_qsl(init_data, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        return None
    if time.time() - auth_date > INIT_DATA_MAX_AGE_SECONDS:
        return None

    user_raw = pairs.get("user")
    if not user_raw:
        return None
    try:
        return json.loads(user_raw)
    except json.JSONDecodeError:
        return None


async def _fetch_and_cache_avatar(tg_id: int) -> Optional[Path]:
    """Telegram profil rasmini yuklab, diskka keshlaydi. Rasm yo'q yoki
    olishning iloji bo'lmasa - buni ham keshlab, qayta-qayta so'rov
    yubormaslik uchun bo'sh marker fayl yaratadi."""
    jpg_path = AVATAR_CACHE_DIR / f"{tg_id}.jpg"
    none_marker = AVATAR_CACHE_DIR / f"{tg_id}.none"
    if jpg_path.exists():
        return jpg_path
    if none_marker.exists():
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{TELEGRAM_API}/getUserProfilePhotos", params={"user_id": tg_id, "limit": 1}
            )
            data = resp.json()
            photos = data.get("result", {}).get("photos") if data.get("ok") else None
            if not photos:
                none_marker.touch()
                return None

            file_id = photos[0][0]["file_id"]  # eng kichik o'lcham - avatar uchun yetarli
            file_resp = await client.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id})
            file_data = file_resp.json()
            if not file_data.get("ok"):
                none_marker.touch()
                return None

            file_path = file_data["result"]["file_path"]
            img_resp = await client.get(f"{TELEGRAM_FILE_URL}/{file_path}")
            if img_resp.status_code != 200:
                none_marker.touch()
                return None

            jpg_path.write_bytes(img_resp.content)
            return jpg_path
    except httpx.HTTPError:
        return None


@app.get("/api/avatar/{tg_id}")
async def avatar(tg_id: int) -> FileResponse:
    path = await _fetch_and_cache_avatar(tg_id)
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


PAGE_SIZE = 50


@app.get("/api/leaderboard")
async def leaderboard(
    x_telegram_init_data: str = Header(default=""),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=PAGE_SIZE, ge=1, le=PAGE_SIZE),
) -> dict:
    """Joriy mavsumdagi TO'LIQ reyting, sahifalab (offset/limit) qaytariladi -
    shu mavsumda ishtirok etgan hamma ko'rinishi mumkin. `you` foydalanuvchining
    haqiqiy o'rnini sahifadan qat'i nazar har doim qaytaradi (pastda "yopishib
    turuvchi" qator sifatida ko'rsatish uchun)."""
    tg_user = _verify_init_data(x_telegram_init_data)

    async with async_session_factory() as session:
        active_season = await SeasonRepo(session).get_active()
        season_service = SeasonService(session)
        referral_repo = ReferralRepo(session)

        total = await referral_repo.season_participant_count(active_season.id)
        rows = await season_service.get_leaderboard_rows(active_season, limit=limit, offset=offset)

        entries = [
            {
                "rank": row["rank"],
                "name": row["name"],
                "count": row["count"],
                "tg_id": row["tg_id"],
                "is_you": bool(tg_user) and row["tg_id"] == tg_user.get("id"),
            }
            for row in rows
        ]

        you = None
        if tg_user:
            user = await UserRepo(session).get_by_tg_id(tg_user["id"])
            if user is not None:
                position = await referral_repo.season_rank_of(active_season.id, user.id)
                if position:
                    you = {
                        "rank": position[0],
                        "count": position[1],
                        "name": user.first_name,
                        "tg_id": user.tg_id,
                    }

        return {
            "season": {"number": active_season.number, "name": active_season.name},
            "total": total,
            "offset": offset,
            "limit": limit,
            "entries": entries,
            "you": you,
        }


@app.get("/api/my-stats")
async def my_stats(x_telegram_init_data: str = Header(default="")) -> dict:
    """Joriy mavsumdagi shaxsiy progress: talab qilingan/tasdiqlangan/
    kutilayotgan/qolgan sonlar, maxfiy kanal holati va reytingdagi o'rni."""
    tg_user = _verify_init_data(x_telegram_init_data)
    if not tg_user:
        raise HTTPException(status_code=401, detail="Telegram orqali ochilishi kerak")

    async with async_session_factory() as session:
        user = await UserRepo(session).get_by_tg_id(tg_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        bot_settings = await SettingsRepo(session).get()
        active_season = await SeasonRepo(session).get_active()
        referral_repo = ReferralRepo(session)
        referral_service = ReferralService(session, SubscriptionService(bot=None))

        progress = await referral_service.get_progress(
            user.id, bot_settings.required_referral_count, active_season.id
        )
        position = await referral_repo.season_rank_of(active_season.id, user.id)

        if user.joined_private_channel:
            channel_status = "joined"
        elif user.secret_link_taken:
            channel_status = "pending"
        else:
            channel_status = "none"

        return {
            "season": {"name": active_season.name},
            "progress": progress,
            "channel_status": channel_status,
            "rank": position[0] if position else None,
        }
