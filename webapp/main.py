import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bot.config import settings
from bot.db.session import async_session_factory
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.user_repo import UserRepo
from bot.services.season_service import SeasonService

INIT_DATA_MAX_AGE_SECONDS = 86400

STATIC_DIR = Path(__file__).parent / "static"

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


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/leaderboard")
async def leaderboard(x_telegram_init_data: str = Header(default="")) -> dict:
    tg_user = _verify_init_data(x_telegram_init_data)

    async with async_session_factory() as session:
        active_season = await SeasonRepo(session).get_active()
        season_service = SeasonService(session)
        rows = await season_service.get_leaderboard_rows(active_season, limit=20)

        entries = [
            {
                "rank": row["rank"],
                "name": row["name"],
                "count": row["count"],
                "is_you": bool(tg_user) and row["tg_id"] == tg_user.get("id"),
            }
            for row in rows
        ]

        you = None
        if tg_user:
            user = await UserRepo(session).get_by_tg_id(tg_user["id"])
            already_in_top = user is not None and any(e["is_you"] for e in entries)
            if user is not None and not already_in_top:
                position = await ReferralRepo(session).season_rank_of(active_season.id, user.id)
                if position:
                    you = {"rank": position[0], "count": position[1], "name": user.first_name}

        return {
            "season": {"number": active_season.number, "name": active_season.name},
            "entries": entries,
            "you": you,
        }
