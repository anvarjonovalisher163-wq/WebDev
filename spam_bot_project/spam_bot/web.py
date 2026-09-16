from aiohttp import web

from spam_bot.db.session import async_session_factory
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.services.crypto_service import CryptoService
from spam_bot.services.key_link_service import key_link_service

_FORM_HTML = """<!doctype html>
<html lang="uz"><head><meta charset="utf-8">
<title>Gemini API kalitini saqlash</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: sans-serif; max-width: 480px; margin: 40px auto; padding: 0 16px; }}
input {{ width: 100%; padding: 10px; margin: 8px 0; box-sizing: border-box; }}
button {{ padding: 10px 20px; }}
.msg {{ padding: 12px; border-radius: 6px; }}
.ok {{ background: #e6ffed; }}
.err {{ background: #ffecec; }}
</style></head>
<body>
<h2>Gemini API kalitini saqlash</h2>
<p>Bu havola bir martalik va 15 daqiqadan so'ng amal qilmay qoladi. Kalit saqlash
vaqtida shifrlanadi va faqat sizning guruhingiz uchun ishlatiladi.</p>
{content}
</body></html>"""


def _render(content: str) -> str:
    return _FORM_HTML.format(content=content)


async def handle_get(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    pending = key_link_service.peek(token)
    if pending is None:
        return web.Response(text=_render('<p class="msg err">Havola muddati o\'tgan yoki noto\'g\'ri.</p>'), content_type="text/html", status=404)
    form = f"""
    <form method="post">
      <input type="password" name="api_key" placeholder="Gemini API kaliti" required autofocus>
      <button type="submit">Saqlash</button>
    </form>
    """
    return web.Response(text=_render(form), content_type="text/html")


async def handle_post(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    pending = key_link_service.consume(token)
    if pending is None:
        return web.Response(text=_render('<p class="msg err">Havola muddati o\'tgan yoki noto\'g\'ri.</p>'), content_type="text/html", status=404)

    data = await request.post()
    api_key = str(data.get("api_key", "")).strip()
    if not api_key:
        return web.Response(text=_render('<p class="msg err">Kalit bo\'sh bo\'lishi mumkin emas.</p>'), content_type="text/html", status=400)

    crypto: CryptoService = request.app["crypto"]
    encrypted = crypto.encrypt(api_key)

    async with async_session_factory() as session:
        repo = GroupRepo(session)
        group = await repo.get_by_chat_id(pending.chat_id)
        if group is None:
            return web.Response(text=_render('<p class="msg err">Guruh topilmadi.</p>'), content_type="text/html", status=404)
        await repo.set_gemini_key(group, encrypted)
        await session.commit()

    return web.Response(text=_render('<p class="msg ok">Kalit muvaffaqiyatli saqlandi. Ushbu sahifani yopishingiz mumkin.</p>'), content_type="text/html")


def create_web_app(crypto: CryptoService) -> web.Application:
    app = web.Application()
    app["crypto"] = crypto
    app.router.add_get("/setkey/{token}", handle_get)
    app.router.add_post("/setkey/{token}", handle_post)
    return app
