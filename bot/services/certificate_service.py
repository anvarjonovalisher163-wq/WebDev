import io
import math
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
LOGO_PATH = ASSETS_DIR / "images" / "uchqun_logo.png"
MEDAL_PATH = ASSETS_DIR / "images" / "uchqun_medal.png"

# A4 albom (landscape) nisbati - 297x210mm, taxminan 150dpi
W, H = 1754, 1240

WHITE = (255, 255, 255)
CREAM = (247, 248, 250)
NAVY = (7, 25, 68)
NAVY2 = (13, 40, 100)
ACCENT = (42, 120, 200)
GRAY = (110, 118, 132)
BODY_GRAY = (75, 82, 96)
LINE_GRAY = (200, 206, 218)
GOLD = (196, 155, 74)

DEFAULT_ACCEPTANCE_TEXT = "🎉 Tabriklaymiz, {ism}! Siz UCHQUN loyihasiga qabul qilindingiz."
DEFAULT_CERTIFICATE_SUBTITLE = "ISHTIROK ETGANLIK SERTIFIKATI"
DEFAULT_CERTIFICATE_BODY_TEXT = (
    "Ushbu sertifikat \"{mavsum}\" davomida UCHQUN loyihasida faol ishtirok etib, "
    "barcha shartlarni muvaffaqiyatli bajargani uchun topshiriladi."
)
DEFAULT_CERTIFICATE_SIGNATURE_NAME = "UCHQUN jamoasi"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS_DIR / name), size)


def _tracked_text(draw, x, y, text, fnt, fill, tracking=0):
    if not tracking:
        draw.text((x, y), text, font=fnt, fill=fill)
        return
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += draw.textlength(ch, font=fnt) + tracking


def _draw_star(draw, cx, cy, r_outer, r_inner, color):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=color)


def _wrap_text(draw, text, fnt, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=fnt) > max_width:
            if current:
                lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def _draw_background(draw: ImageDraw.ImageDraw) -> None:
    """Ikkita ustma-ust doira yordamida na'muna dizayndagi organik
    ko'k/oq "to'lqin" fonni chizadi (logotip rangiga moslangan)."""
    draw.ellipse(
        [W * 0.16, -H * 0.55, W * 1.30, H * 0.85],
        fill=NAVY,
    )
    draw.ellipse(
        [-W * 0.18, H * 0.06, W * 0.86, H * 1.55],
        fill=CREAM,
    )


def render_certificate(
    full_name: str,
    subtitle: str,
    body_text: str,
    signature_name: str,
    issued_date: date,
) -> Image.Image:
    """UCHQUN loyihasi sertifikatini (PIL Image, A4 albom) chizadi."""
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    _draw_background(draw)

    margin_x = 130

    f_title = _font("Outfit-Bold.ttf", 42)
    f_subtitle = _font("Outfit-Bold.ttf", 19)
    f_name = _font("Outfit-Bold.ttf", 58)
    f_body = _font("Outfit-Regular.ttf", 22)
    f_meta_label = _font("Outfit-Bold.ttf", 17)
    f_date_value = _font("Outfit-Bold.ttf", 20)
    f_signature = _font("Outfit-Bold.ttf", 30)

    # --- Yuqori-o'ng (ko'k) blokdagi sarlavha ---
    title_x = W - margin_x - 40
    ty = 90
    title_line = "SERTIFIKAT"
    title_w = draw.textlength(title_line, font=f_title) + len(title_line) * 6
    _tracked_text(draw, title_x - title_w, ty, title_line, f_title, WHITE, tracking=6)
    ty += 62
    sub_lines = _wrap_text(draw, subtitle.upper(), f_subtitle, 420)
    for line in sub_lines[:2]:
        w = draw.textlength(line, font=f_subtitle) + len(line) * 3
        _tracked_text(draw, title_x - w, ty, line, f_subtitle, WHITE, tracking=3)
        ty += 32

    # --- Nishon (medal, foydalanuvchi yuborgan rasm) - "TAQDIM ETILADI" tepasida ---
    if MEDAL_PATH.exists():
        medal = Image.open(MEDAL_PATH).convert("RGBA")
        medal_w = 210
        medal_h = int(medal.height * medal_w / medal.width)
        medal_resized = medal.resize((medal_w, medal_h), Image.LANCZOS)
        medal_x, medal_y = margin_x, 210
        img.paste(medal_resized, (medal_x, medal_y), medal_resized)

        star_cx = medal_x + medal_w * 0.5
        star_cy = medal_y + medal_h * 0.372
        star_r = medal_w * 0.135
        _draw_star(draw, star_cx, star_cy, star_r, star_r * 0.42, GOLD)

    # --- Logotip (pastda, yorug' fonda) ---
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 190
        logo_h = int(logo.height * logo_w / logo.width)
        logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)
        img.paste(logo_resized, (margin_x, H - 110), logo_resized)

    # --- Ism va matn (chapga tekislangan) ---
    content_x = margin_x
    y = 560
    _tracked_text(draw, content_x, y, "TAQDIM ETILADI:", f_meta_label, GRAY, tracking=3)
    y += 42
    draw.text((content_x, y), full_name, font=f_name, fill=NAVY)
    y += 96

    max_width = W * 0.5
    for line in _wrap_text(draw, body_text, f_body, max_width):
        draw.text((content_x, y), line, font=f_body, fill=BODY_GRAY)
        y += 36

    y += 18
    draw.text(
        (content_x, y),
        f"Berilgan sana: {issued_date.strftime('%d.%m.%Y')}",
        font=f_date_value, fill=NAVY,
    )

    # --- Imzo bloki ---
    if signature_name:
        sig_y = H - 210
        sig_w = 340
        draw.text((content_x, sig_y - 42), signature_name, font=f_signature, fill=NAVY2)
        draw.line([(content_x, sig_y), (content_x + sig_w, sig_y)], fill=LINE_GRAY, width=1)
        _tracked_text(draw, content_x, sig_y + 14, "LOYIHA MUALLIFI", f_meta_label, GRAY, tracking=2)

    return img


def render_certificate_png(
    full_name: str,
    subtitle: str,
    body_text: str,
    signature_name: str,
    issued_date: date,
) -> bytes:
    img = render_certificate(full_name, subtitle, body_text, signature_name, issued_date)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
