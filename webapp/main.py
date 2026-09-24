import hashlib
import hmac
import io
import json
import secrets
import time
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode
from zoneinfo import ZoneInfo

import httpx
from fastapi import Body, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from bot.config import settings
from bot.db.session import async_session_factory
from bot.models.marra_campaign import MarraCampaign
from bot.models.referral import ReferralStatus
from bot.repositories.admin_repo import AdminRepo
from bot.repositories.auth_flow_repo import (
    MAX_OTP_ATTEMPTS,
    OAUTH_STATE_TTL_MINUTES,
    OTP_TTL_MINUTES,
    AuthFlowRepo,
)
from bot.repositories.marra_campaign_repo import MarraCampaignRepo
from bot.repositories.marra_participant_repo import MarraParticipantRepo
from bot.repositories.marra_progress_repo import MarraProgressRepo
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_identity_repo import UserIdentityRepo
from bot.repositories.user_repo import UserRepo
from bot.repositories.web_session_repo import (
    SESSION_TTL_DAYS,
    WebLoginTokenRepo,
    WebSessionRepo,
)
from bot.services.certificate_service import (
    DEFAULT_ACCEPTANCE_TEXT,
    DEFAULT_CERTIFICATE_BODY_TEXT,
    DEFAULT_CERTIFICATE_SIGNATURE_NAME,
    DEFAULT_CERTIFICATE_SUBTITLE,
    render_certificate_png,
)
from bot.services.email_service import send_login_code_email
from bot.services.referral_service import ReferralService
from bot.services.season_service import SeasonService
from bot.services.sms_service import send_otp_sms
from bot.services.subscription_service import SubscriptionService

TASHKENT_TZ = ZoneInfo("Asia/Tashkent")
SESSION_COOKIE_NAME = "uchqun_session"

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


@app.get("/admin")
async def admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


# "Literal" dizayn uslubidagi landing sahifa (statik, API'ga bog'lanmagan).
@app.get("/literal")
async def literal_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "literal.html")


# UCHQUN 2.0 - Marra (o'qish marafoni). Hozircha hech qayerdan (index.html,
# admin.html, bot menyusi) link berilmagan - faqat to'g'ridan-to'g'ri URL
# bilan va faqat admin sifatida ochish mumkin (pastdagi barcha /api/marra2/*
# va /api/admin/marra2/* endpointlar ham admin talab qiladi). UCHQUN 1.0
# foydalanuvchilariga butunlay ko'rinmaydi va ular bilan hech qanday
# aloqasi yo'q (eski Marra - settings.marra_url va h.k. - o'zgarishsiz qoladi).
@app.get("/marra2-admin")
async def marra2_admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "marra2_admin.html")


@app.get("/marra2")
async def marra2_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "marra2.html")


# Telegram ichida ochilganda initData orqali, Telegram'dan TASHQARIDA
# (oddiy brauzer/PWA) ochilganda esa /login orqali o'rnatilgan sessiya
# cookie orqali autentifikatsiya qilinadi. `request` berilmasa (eski
# chaqiruvlar), faqat initData tekshiriladi - orqaga mos.
async def _authenticate(init_data: str, session, request: Optional[Request] = None) -> Optional[dict]:
    tg_user = _verify_init_data(init_data)
    if tg_user:
        return tg_user
    if request is None:
        return None

    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_token:
        return None
    token_hash = hashlib.sha256(cookie_token.encode()).hexdigest()
    web_session = await WebSessionRepo(session).get_valid(token_hash)
    if web_session is None:
        return None

    user = await UserRepo(session).get_by_id(web_session.user_id)
    if user is None:
        return None
    return {"id": user.tg_id, "first_name": user.first_name, "username": user.username}


async def _require_admin(init_data: str, session, request: Optional[Request] = None) -> dict:
    tg_user = await _authenticate(init_data, session, request)
    if not tg_user:
        raise HTTPException(status_code=401, detail="Telegram orqali ochilishi kerak")
    admin = await AdminRepo(session).get_by_tg_id(tg_user["id"])
    if admin is None:
        raise HTTPException(status_code=403, detail="Sizda admin huquqi yo'q")
    return tg_user


async def _issue_web_session(session, user_id: int) -> str:
    """Foydalanuvchi uchun yangi uzoq muddatli veb-sessiya yaratadi va
    brauzerga qo'yiladigan xom tokenni qaytaradi (bazada faqat hash saqlanadi)."""
    session_token = secrets.token_urlsafe(32)
    session_hash = hashlib.sha256(session_token.encode()).hexdigest()
    await WebSessionRepo(session).create(user_id, session_hash)
    return session_token


def _set_session_cookie(response, session_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_TTL_DAYS * 86400,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


_bot_username_cache: Optional[str] = None


async def _get_bot_username() -> str:
    global _bot_username_cache
    if _bot_username_cache:
        return _bot_username_cache
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{TELEGRAM_API}/getMe")
            data = resp.json()
    except httpx.HTTPError:
        return ""
    if data.get("ok"):
        _bot_username_cache = data["result"]["username"]
        return _bot_username_cache
    return ""


def _verify_telegram_login_widget(params: dict) -> Optional[dict]:
    """Telegram Login Widget'ning rasmiy tekshiruv algoritmi - WebApp
    initData'nikidan farqli: maxfiy kalit SHA256(bot_token), HMAC 'hash'
    maydonisiz qolgan barcha maydonlardan hisoblanadi."""
    received_hash = params.get("hash")
    if not received_hash:
        return None
    check_pairs = {k: v for k, v in params.items() if k != "hash"}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(check_pairs.items()))
    secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return None
    try:
        auth_date = int(params.get("auth_date", "0"))
    except ValueError:
        return None
    if time.time() - auth_date > INIT_DATA_MAX_AGE_SECONDS:
        return None
    return params


@app.get("/login")
async def web_login(t: Optional[str] = Query(default=None)) -> Response:
    """`t` bilan - bot /webapp orqali bergan bir martalik tokenni tekshiradi
    va sessiya o'rnatadi (eski oqim). `t`siz - Mutolaa uslubidagi to'liq
    login sahifasini ko'rsatadi (Telegram, Google, telefon, email)."""
    if t is None:
        bot_username = await _get_bot_username()
        html = (STATIC_DIR / "login.html").read_text(encoding="utf-8")
        html = html.replace("{{BOT_USERNAME}}", bot_username)
        html = html.replace("{{GOOGLE_ENABLED}}", "true" if settings.google_oauth_configured else "false")
        html = html.replace("{{EMAIL_ENABLED}}", "true" if settings.smtp_configured else "false")
        html = html.replace("{{PHONE_ENABLED}}", "true" if settings.eskiz_configured else "false")
        return Response(content=html, media_type="text/html")

    token_hash = hashlib.sha256(t.encode()).hexdigest()

    async with async_session_factory() as session:
        token_repo = WebLoginTokenRepo(session)
        login_token = await token_repo.get_valid(token_hash)
        if login_token is None:
            raise HTTPException(status_code=400, detail="Havola eskirgan yoki allaqachon ishlatilgan")
        await token_repo.mark_used(login_token)
        session_token = await _issue_web_session(session, login_token.user_id)
        await session.commit()

    response = RedirectResponse(url="/")
    _set_session_cookie(response, session_token)
    return response


def _safe_next_path(raw: Optional[str]) -> str:
    """Faqat shu saytning o'z ichidagi yo'lga qaytarishga ruxsat beradi -
    tashqi manzilga (open redirect) yo'naltirishning oldini oladi."""
    if not raw or not raw.startswith("/") or raw.startswith("//") or "://" in raw:
        return "/"
    return raw


@app.get("/auth/telegram/callback")
async def telegram_login_callback(request: Request) -> RedirectResponse:
    """Telegram Login Widget muvaffaqiyatli autentifikatsiyadan so'ng shu
    yerga qaytaradi (GET query parametrlari bilan)."""
    params = dict(request.query_params)
    next_path = _safe_next_path(params.pop("next", None))

    tg_data = _verify_telegram_login_widget(params)
    if tg_data is None:
        raise HTTPException(status_code=401, detail="Telegram autentifikatsiyasi noto'g'ri")

    async with async_session_factory() as session:
        user = await UserRepo(session).get_by_tg_id(int(tg_data["id"]))
        if user is None:
            # Foydalanuvchi hali botga /start bosmagan - avval shu shart
            # bajarilishi kerak (referral/obuna tizimi shunga bog'liq).
            return RedirectResponse(url="/login?error=start_bot_first")

        session_token = await _issue_web_session(session, user.id)
        await session.commit()

    response = RedirectResponse(url=next_path)
    _set_session_cookie(response, session_token)
    return response


async def _current_internal_user_id(request: Request, session) -> Optional[int]:
    """Hozir link qilinayotgan email/telefon/Google qaysi hisobga
    biriktirilishi kerakligini aniqlaydi - faqat allaqachon (cookie orqali)
    kirgan foydalanuvchi uchun ishlaydi, aks holda None."""
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_token:
        return None
    token_hash = hashlib.sha256(cookie_token.encode()).hexdigest()
    web_session = await WebSessionRepo(session).get_valid(token_hash)
    return web_session.user_id if web_session else None


async def _verify_otp_and_login(kind: str, provider: str, address: str, code: str) -> str:
    """OTP kodni tekshiradi va mos hisob bilan (allaqachon bog'langan bo'lsa)
    kirishni, yoki (link so'ralgan bo'lsa) yangi bog'lashni amalga oshiradi.
    Muvaffaqiyatli bo'lsa yangi sessiya tokenini qaytaradi."""
    async with async_session_factory() as session:
        auth_repo = AuthFlowRepo(session)
        state = await auth_repo.get_active_by_address(kind, address)
        if state is None:
            raise HTTPException(status_code=400, detail="Kod eskirgan, qaytadan so'rang")
        if state.attempts >= MAX_OTP_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Urinishlar soni tugadi, qaytadan so'rang")

        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if not hmac.compare_digest(state.token_hash, code_hash):
            await auth_repo.increment_attempts(state)
            await session.commit()
            raise HTTPException(status_code=400, detail="Kod noto'g'ri")

        await auth_repo.mark_used(state)

        identity_repo = UserIdentityRepo(session)
        identity = await identity_repo.get(provider, address)
        if identity is not None:
            user_id = identity.user_id
        elif state.linking_user_id is not None:
            await identity_repo.link(state.linking_user_id, provider, address)
            user_id = state.linking_user_id
        else:
            await session.commit()
            label = "email" if provider == "email" else "raqam"
            raise HTTPException(
                status_code=404,
                detail=f"Bu {label} hech qaysi hisobga bog'lanmagan. Avval Telegram orqali kiring.",
            )

        session_token = await _issue_web_session(session, user_id)
        await session.commit()
        return session_token


@app.post("/auth/email/request")
async def email_login_request(request: Request, payload: dict = Body(...)) -> dict:
    email = (payload.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email noto'g'ri")
    if not settings.smtp_configured:
        raise HTTPException(status_code=503, detail="Email orqali kirish hali sozlanmagan")

    async with async_session_factory() as session:
        linking_user_id = await _current_internal_user_id(request, session)
        code = f"{secrets.randbelow(1000000):06d}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        await AuthFlowRepo(session).create(
            kind="otp_email",
            token_hash=code_hash,
            address=email,
            linking_user_id=linking_user_id,
            ttl_minutes=OTP_TTL_MINUTES,
        )
        await session.commit()

    if not await send_login_code_email(email, code):
        raise HTTPException(status_code=502, detail="Email yuborib bo'lmadi")
    return {"ok": True}


@app.post("/auth/email/verify")
async def email_login_verify(payload: dict = Body(...)) -> Response:
    email = (payload.get("email") or "").strip().lower()
    code = (payload.get("code") or "").strip()
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email va kod kerak")

    session_token = await _verify_otp_and_login("otp_email", "email", email, code)
    response = Response(content='{"ok": true}', media_type="application/json")
    _set_session_cookie(response, session_token)
    return response


@app.post("/auth/phone/request")
async def phone_login_request(request: Request, payload: dict = Body(...)) -> dict:
    phone = (payload.get("phone") or "").strip()
    if not phone.startswith("+") or len(phone) < 9:
        raise HTTPException(status_code=400, detail="Telefon raqam noto'g'ri (masalan: +998901234567)")
    if not settings.eskiz_configured:
        raise HTTPException(status_code=503, detail="Telefon orqali kirish hali sozlanmagan")

    async with async_session_factory() as session:
        linking_user_id = await _current_internal_user_id(request, session)
        code = f"{secrets.randbelow(1000000):06d}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        await AuthFlowRepo(session).create(
            kind="otp_phone",
            token_hash=code_hash,
            address=phone,
            linking_user_id=linking_user_id,
            ttl_minutes=OTP_TTL_MINUTES,
        )
        await session.commit()

    if not await send_otp_sms(phone, code):
        raise HTTPException(status_code=502, detail="SMS yuborib bo'lmadi")
    return {"ok": True}


@app.post("/auth/phone/verify")
async def phone_login_verify(payload: dict = Body(...)) -> Response:
    phone = (payload.get("phone") or "").strip()
    code = (payload.get("code") or "").strip()
    if not phone or not code:
        raise HTTPException(status_code=400, detail="Telefon va kod kerak")

    session_token = await _verify_otp_and_login("otp_phone", "phone", phone, code)
    response = Response(content='{"ok": true}', media_type="application/json")
    _set_session_cookie(response, session_token)
    return response


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


@app.get("/auth/google/start")
async def google_login_start(request: Request, next: str = Query(default="/")) -> RedirectResponse:
    if not settings.google_oauth_configured:
        raise HTTPException(status_code=503, detail="Google orqali kirish hali sozlanmagan")

    async with async_session_factory() as session:
        linking_user_id = await _current_internal_user_id(request, session)
        state_value = secrets.token_urlsafe(24)
        state_hash = hashlib.sha256(state_value.encode()).hexdigest()
        await AuthFlowRepo(session).create(
            kind="oauth_google",
            token_hash=state_hash,
            linking_user_id=linking_user_id,
            next_path=_safe_next_path(next),
            ttl_minutes=OAUTH_STATE_TTL_MINUTES,
        )
        await session.commit()

    redirect_uri = f"{settings.webapp_url}/auth/google/callback"
    query = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state_value,
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(query)}")


@app.get("/auth/google/callback")
async def google_login_callback(
    code: str = Query(default=""), state: str = Query(default=""), error: str = Query(default="")
) -> RedirectResponse:
    if error or not code or not state:
        return RedirectResponse(url="/login?error=google_failed")

    state_hash = hashlib.sha256(state.encode()).hexdigest()
    async with async_session_factory() as session:
        auth_repo = AuthFlowRepo(session)
        flow_state = await auth_repo.get_valid("oauth_google", state_hash)
        if flow_state is None:
            return RedirectResponse(url="/login?error=google_failed")
        await auth_repo.mark_used(flow_state)

        redirect_uri = f"{settings.webapp_url}/auth/google/callback"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                token_resp = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    return RedirectResponse(url="/login?error=google_failed")

                userinfo_resp = await client.get(
                    GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
                )
                userinfo = userinfo_resp.json()
        except httpx.HTTPError:
            return RedirectResponse(url="/login?error=google_failed")

        google_sub = userinfo.get("sub")
        if not google_sub:
            return RedirectResponse(url="/login?error=google_failed")

        identity_repo = UserIdentityRepo(session)
        identity = await identity_repo.get("google", google_sub)
        if identity is not None:
            user_id = identity.user_id
        elif flow_state.linking_user_id is not None:
            await identity_repo.link(flow_state.linking_user_id, "google", google_sub)
            user_id = flow_state.linking_user_id
        else:
            await session.commit()
            return RedirectResponse(url="/login?error=start_bot_first")

        session_token = await _issue_web_session(session, user_id)
        await session.commit()
        next_path = flow_state.next_path or "/"

    response = RedirectResponse(url=next_path)
    _set_session_cookie(response, session_token)
    return response


@app.get("/api/admin/certificate")
async def get_certificate_settings(x_telegram_init_data: str = Header(default="")) -> dict:
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session)
        bot_settings = await SettingsRepo(session).get()
        season = await SeasonRepo(session).get_active()

        return {
            "acceptance_text": bot_settings.acceptance_text or "",
            "certificate_subtitle": bot_settings.certificate_subtitle or "",
            "certificate_body_text": bot_settings.certificate_body_text or "",
            "certificate_signature_name": bot_settings.certificate_signature_name or "",
            "defaults": {
                "acceptance_text": DEFAULT_ACCEPTANCE_TEXT,
                "certificate_subtitle": DEFAULT_CERTIFICATE_SUBTITLE,
                "certificate_body_text": DEFAULT_CERTIFICATE_BODY_TEXT,
                "certificate_signature_name": DEFAULT_CERTIFICATE_SIGNATURE_NAME,
            },
            "season_name": season.name if season else "",
        }


@app.post("/api/admin/certificate")
async def save_certificate_settings(
    payload: dict = Body(...), x_telegram_init_data: str = Header(default="")
) -> dict:
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session)
        bot_settings = await SettingsRepo(session).get()

        bot_settings.acceptance_text = (payload.get("acceptance_text") or "").strip() or None
        bot_settings.certificate_subtitle = (payload.get("certificate_subtitle") or "").strip() or None
        bot_settings.certificate_body_text = (payload.get("certificate_body_text") or "").strip() or None
        bot_settings.certificate_signature_name = (
            payload.get("certificate_signature_name") or ""
        ).strip() or None

        await session.commit()
        return {"ok": True}


@app.get("/api/admin/certificate/preview")
async def certificate_preview(
    init_data: str = Query(default=""),
    full_name: str = Query(default="Anvar Anvarov"),
    subtitle: str = Query(default=""),
    body_text: str = Query(default=""),
    signature_name: str = Query(default=""),
) -> Response:
    async with async_session_factory() as session:
        await _require_admin(init_data, session)
        season = await SeasonRepo(session).get_active()

    season_name = season.name if season else ""
    resolved_subtitle = subtitle.strip() or DEFAULT_CERTIFICATE_SUBTITLE
    resolved_body = (body_text.strip() or DEFAULT_CERTIFICATE_BODY_TEXT).replace("{mavsum}", season_name)
    resolved_signature = signature_name.strip() or DEFAULT_CERTIFICATE_SIGNATURE_NAME

    png = render_certificate_png(
        full_name.strip() or "Anvar Anvarov",
        resolved_subtitle,
        resolved_body,
        resolved_signature,
        datetime.now(timezone.utc).date(),
    )
    return Response(content=png, media_type="image/png")


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
        is_admin = False
        if tg_user:
            is_admin = await AdminRepo(session).get_by_tg_id(tg_user["id"]) is not None

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
            "is_admin": is_admin,
        }


@app.get("/api/admin/user-referrals/{tg_id}")
async def admin_user_referrals(
    tg_id: int, x_telegram_init_data: str = Header(default="")
) -> dict:
    """Admin - berilgan foydalanuvchi joriy mavsumda kimlarni taklif
    qilganini (holati bilan) ko'rish uchun, reytingdagi profilga bosganda."""
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session)

        user_repo = UserRepo(session)
        target = await user_repo.get_by_tg_id(tg_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        active_season = await SeasonRepo(session).get_active()
        referral_repo = ReferralRepo(session)
        referrals = await referral_repo.list_by_referrer_in_season(target.id, active_season.id)

        items = []
        for referral in referrals:
            referred = await user_repo.get_by_id(referral.referred_id)
            referred_count = 0
            if referred is not None:
                referred_count = await referral_repo.count_by_referrer_and_status_in_season(
                    referred.id, ReferralStatus.APPROVED, active_season.id
                )
            items.append(
                {
                    "name": referred.first_name if referred else "?",
                    "username": referred.username if referred else None,
                    "tg_id": referred.tg_id if referred else None,
                    "status": referral.status.value,
                    "referred_count": referred_count,
                }
            )

        return {"name": target.first_name, "referrals": items}


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


# ============================================================================
# UCHQUN 2.0 - Marra (o'qish marafoni), Mutolaa'dagi mexanizmga o'xshab:
# ishtirokchi kitobni shu Mini App ichida o'qiydi, sahifa faol/ko'rinib
# turgan vaqt avtomatik hisoblanadi (heartbeat), kunlik talab bajarilmasa
# ishtirokchi avtomatik chiqariladi (bot/jobs/marra2_elimination.py).
#
# HOZIRCHA HAMMA ENDPOINT (ishtirokchi tomoni ham) _require_admin bilan
# cheklangan - chunki bu hali sinov bosqichida va UCHQUN 1.0
# foydalanuvchilariga ko'rinmasligi kerak. Ommaga ochish payti kelganda,
# ishtirokchi endpointlaridagi _require_admin chaqiruvini oddiy
# Telegram-autentifikatsiyaga (faqat _verify_init_data, admin tekshiruvisiz)
# almashtirish kifoya.
# ============================================================================


def _marra2_day_number(campaign: MarraCampaign, on_date: date_type) -> int:
    return (on_date - campaign.start_date).days + 1


def _marra2_campaign_summary(campaign: MarraCampaign) -> dict:
    return {
        "id": campaign.id,
        "title": campaign.title,
        "description": campaign.description,
        "prize_text": campaign.prize_text,
        "book_title": campaign.book_title,
        "day_count": campaign.day_count,
        "daily_minutes_required": campaign.daily_minutes_required,
        "start_date": campaign.start_date.isoformat(),
        "end_date": (campaign.start_date + timedelta(days=campaign.day_count - 1)).isoformat(),
        "is_active": campaign.is_active,
    }


@app.get("/api/admin/marra2/campaigns")
async def marra2_list_campaigns(
    request: Request, x_telegram_init_data: str = Header(default="")
) -> dict:
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session, request)
        campaign_repo = MarraCampaignRepo(session)
        participant_repo = MarraParticipantRepo(session)

        items = []
        for campaign in await campaign_repo.list_all():
            item = _marra2_campaign_summary(campaign)
            item["participant_count"] = await participant_repo.count_by_campaign(campaign.id)
            item["active_participant_count"] = await participant_repo.count_by_campaign(
                campaign.id, eliminated=False
            )
            items.append(item)
        return {"campaigns": items}


@app.post("/api/admin/marra2/campaigns")
async def marra2_create_campaign(
    request: Request, payload: dict = Body(...), x_telegram_init_data: str = Header(default="")
) -> dict:
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session, request)

        title = (payload.get("title") or "").strip()
        book_title = (payload.get("book_title") or "").strip()
        book_text = (payload.get("book_text") or "").strip()
        try:
            day_count = int(payload.get("day_count") or 0)
            daily_minutes_required = int(payload.get("daily_minutes_required") or 0)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Kunlar soni va daqiqa butun son bo'lishi kerak")

        if not title or not book_title or not book_text:
            raise HTTPException(status_code=400, detail="Sarlavha, kitob nomi va matni majburiy")
        if day_count < 1 or daily_minutes_required < 1:
            raise HTTPException(
                status_code=400, detail="Kunlar soni va kunlik daqiqa 1 dan katta bo'lishi kerak"
            )
        try:
            start_date = date_type.fromisoformat((payload.get("start_date") or "").strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Boshlanish sanasi noto'g'ri (YYYY-MM-DD)")

        campaign = await MarraCampaignRepo(session).create(
            title=title,
            description=(payload.get("description") or "").strip() or None,
            prize_text=(payload.get("prize_text") or "").strip() or None,
            book_title=book_title,
            book_text=book_text,
            day_count=day_count,
            daily_minutes_required=daily_minutes_required,
            start_date=start_date,
        )
        await session.commit()
        return _marra2_campaign_summary(campaign)


@app.patch("/api/admin/marra2/campaigns/{campaign_id}")
async def marra2_toggle_campaign(
    campaign_id: int,
    request: Request,
    payload: dict = Body(...),
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session, request)
        campaign_repo = MarraCampaignRepo(session)
        campaign = await campaign_repo.get_by_id(campaign_id)
        if campaign is None:
            raise HTTPException(status_code=404, detail="Kampaniya topilmadi")

        if "is_active" in payload:
            await campaign_repo.set_active(campaign, bool(payload["is_active"]))
        await session.commit()
        return _marra2_campaign_summary(campaign)


@app.get("/api/admin/marra2/campaigns/{campaign_id}/participants")
async def marra2_campaign_participants(
    campaign_id: int, request: Request, x_telegram_init_data: str = Header(default="")
) -> dict:
    async with async_session_factory() as session:
        await _require_admin(x_telegram_init_data, session, request)
        campaign = await MarraCampaignRepo(session).get_by_id(campaign_id)
        if campaign is None:
            raise HTTPException(status_code=404, detail="Kampaniya topilmadi")

        participant_repo = MarraParticipantRepo(session)
        progress_repo = MarraProgressRepo(session)
        user_repo = UserRepo(session)

        today_day = _marra2_day_number(campaign, datetime.now(TASHKENT_TZ).date())
        rows = []
        for participant in await participant_repo.list_by_campaign(campaign_id):
            user = await user_repo.get_by_id(participant.user_id)
            progress_list = await progress_repo.list_by_participant(participant.id)
            rows.append(
                {
                    "user_id": participant.user_id,
                    "name": user.first_name if user else "?",
                    "username": user.username if user else None,
                    "joined_at": participant.joined_at.isoformat(),
                    "is_eliminated": participant.is_eliminated,
                    "eliminated_on_day": participant.eliminated_on_day,
                    "completed_days": sorted(p.day_number for p in progress_list if p.completed),
                }
            )

        return {
            "campaign": _marra2_campaign_summary(campaign),
            "today_day_number": today_day,
            "participants": rows,
        }


@app.get("/api/marra2/campaigns/{campaign_id}")
async def marra2_campaign_detail(
    campaign_id: int, request: Request, init_data: str = Query(default="")
) -> dict:
    async with async_session_factory() as session:
        tg_user = await _require_admin(init_data, session, request)
        campaign = await MarraCampaignRepo(session).get_by_id(campaign_id)
        if campaign is None or not campaign.is_active:
            raise HTTPException(status_code=404, detail="Marra topilmadi")

        user = await UserRepo(session).get_by_tg_id(tg_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        participant = await MarraParticipantRepo(session).get(campaign_id, user.id)
        today_day = _marra2_day_number(campaign, datetime.now(TASHKENT_TZ).date())

        progress_today = None
        if participant is not None and 1 <= today_day <= campaign.day_count:
            progress_today = await MarraProgressRepo(session).get(participant.id, today_day)

        result = _marra2_campaign_summary(campaign)
        result["book_text"] = campaign.book_text
        result["today_day_number"] = today_day
        result["joined"] = participant is not None
        result["is_eliminated"] = participant.is_eliminated if participant else False
        result["seconds_read_today"] = progress_today.seconds_read if progress_today else 0
        result["required_seconds"] = campaign.daily_minutes_required * 60
        result["completed_today"] = progress_today.completed if progress_today else False
        return result


@app.post("/api/marra2/campaigns/{campaign_id}/join")
async def marra2_join_campaign(
    campaign_id: int, request: Request, x_telegram_init_data: str = Header(default="")
) -> dict:
    async with async_session_factory() as session:
        tg_user = await _require_admin(x_telegram_init_data, session, request)
        campaign = await MarraCampaignRepo(session).get_by_id(campaign_id)
        if campaign is None or not campaign.is_active:
            raise HTTPException(status_code=404, detail="Marra topilmadi")

        user = await UserRepo(session).get_by_tg_id(tg_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        participant_repo = MarraParticipantRepo(session)
        participant = await participant_repo.get(campaign_id, user.id)
        if participant is None:
            await participant_repo.join(campaign_id, user.id)
            await session.commit()
        return {"ok": True}


@app.post("/api/marra2/campaigns/{campaign_id}/heartbeat")
async def marra2_heartbeat(
    campaign_id: int,
    request: Request,
    payload: dict = Body(...),
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    """Kitob sahifasi ochiq va faol (brauzer tab ko'rinib turgan) paytda
    frontend har necha soniyada shu yerga soniya yuboradi - shu tariqa
    o'qish vaqti avtomatik, Mutolaa'dagi kabi hisoblanadi. Diqqat: hozircha
    bu faqat admin sinovi uchun, chin anti-fraud (masalan so'nggi heartbeat
    vaqtidan oshib ketishni tekshirish) ommaga chiqarishdan oldin qo'shilishi
    kerak."""
    try:
        seconds = int(payload.get("seconds") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Noto'g'ri qiymat")
    if not (0 < seconds <= 30):
        raise HTTPException(status_code=400, detail="Noto'g'ri qiymat")

    async with async_session_factory() as session:
        tg_user = await _require_admin(x_telegram_init_data, session, request)
        campaign = await MarraCampaignRepo(session).get_by_id(campaign_id)
        if campaign is None or not campaign.is_active:
            raise HTTPException(status_code=404, detail="Marra topilmadi")

        user = await UserRepo(session).get_by_tg_id(tg_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        participant_repo = MarraParticipantRepo(session)
        participant = await participant_repo.get(campaign_id, user.id)
        if participant is None:
            raise HTTPException(status_code=403, detail="Avval marraga qo'shiling")
        if participant.is_eliminated:
            raise HTTPException(status_code=403, detail="Siz marradan chiqarilgansiz")

        today_day = _marra2_day_number(campaign, datetime.now(TASHKENT_TZ).date())
        if not (1 <= today_day <= campaign.day_count):
            raise HTTPException(status_code=400, detail="Marra kunlari doirasidan tashqari")

        progress_repo = MarraProgressRepo(session)
        progress = await progress_repo.get_or_create(participant.id, today_day)
        await progress_repo.add_seconds(progress, seconds, campaign.daily_minutes_required)
        await session.commit()

        return {
            "seconds_read": progress.seconds_read,
            "required_seconds": campaign.daily_minutes_required * 60,
            "completed": progress.completed,
        }
