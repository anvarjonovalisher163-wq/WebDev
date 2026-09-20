import io
import math
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
LOGO_PATH = ASSETS_DIR / "images" / "uchqun_logo.png"

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
GOLD_LIGHT = (224, 193, 128)

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


def _draw_leaf(draw, cx, cy, angle, length, width, color):
    """Bitta laur bargi - berilgan burchak bo'yicha cho'zilgan romb shakli."""
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    tip = (cx + dx * length, cy + dy * length)
    base = (cx, cy)
    mid = (cx + dx * length * 0.45, cy + dy * length * 0.45)
    p1 = (mid[0] + nx * width, mid[1] + ny * width)
    p2 = (mid[0] - nx * width, mid[1] - ny * width)
    draw.polygon([base, p1, tip, p2], fill=color)


def _draw_laurel_branch(draw, cx, cy, side, color):
    """Chap (side=-1) yoki o'ng (side=1) tomonga qaragan laur shoxchasi."""
    for i in range(7):
        t = i / 6
        angle = math.pi * (0.62 - 0.30 * t) if side < 0 else math.pi * (0.38 + 0.30 * t)
        r = 34 + t * 40
        leaf_cx = cx + side * r * math.sin(t * 1.0 + 0.2)
        leaf_cy = cy - r * 0.55 + t * 78
        _draw_leaf(draw, leaf_cx, leaf_cy, angle if side < 0 else math.pi - angle, 22, 7, color)


def _draw_medal(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    """Na'muna sifatida yuborilgan ko'k-oltin medal/rozetkaga o'xshash
    nishon chizadi: tishli chegara, oltin halqa, laur shoxchalari va
    markazda yulduzcha."""
    scallop_r = r * 0.22
    for i in range(16):
        angle = 2 * math.pi * i / 16
        bx = cx + r * math.cos(angle)
        by = cy + r * math.sin(angle)
        draw.ellipse([bx - scallop_r, by - scallop_r, bx + scallop_r, by + scallop_r], fill=NAVY)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY)

    ring_r = r * 0.86
    draw.ellipse(
        [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=GOLD, width=max(2, int(r * 0.045))
    )

    inner_r = r * 0.72
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=CREAM)
    draw.ellipse(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], outline=GOLD_LIGHT, width=2
    )

    _draw_laurel_branch(draw, cx, cy, -1, GOLD)
    _draw_laurel_branch(draw, cx, cy, 1, GOLD)
    _draw_star(draw, cx, cy, inner_r * 0.42, inner_r * 0.17, GOLD)

    ribbon_w = r * 0.34
    ribbon_len = r * 1.0
    draw.polygon(
        [
            (cx - ribbon_w * 1.1, cy + r * 0.72),
            (cx - ribbon_w * 0.15, cy + r * 0.72),
            (cx - ribbon_w * 0.05, cy + r * 0.72 + ribbon_len),
            (cx - ribbon_w * 0.9, cy + r * 0.72 + ribbon_len * 0.72),
        ],
        fill=NAVY,
    )
    draw.polygon(
        [
            (cx + ribbon_w * 1.1, cy + r * 0.72),
            (cx + ribbon_w * 0.15, cy + r * 0.72),
            (cx + ribbon_w * 0.05, cy + r * 0.72 + ribbon_len),
            (cx + ribbon_w * 0.9, cy + r * 0.72 + ribbon_len * 0.72),
        ],
        fill=NAVY2,
    )
    draw.line(
        [(cx - ribbon_w * 0.5, cy + r * 0.72), (cx - ribbon_w * 0.35, cy + r * 0.72 + ribbon_len * 0.75)],
        fill=GOLD, width=3,
    )
    draw.line(
        [(cx + ribbon_w * 0.5, cy + r * 0.72), (cx + ribbon_w * 0.35, cy + r * 0.72 + ribbon_len * 0.75)],
        fill=GOLD, width=3,
    )


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

    f_title = _font("Lora-Bold.ttf", 40)
    f_subtitle = _font("Lora-Bold.ttf", 20)
    f_name = _font("Lora-Bold.ttf", 64)
    f_body = _font("Lora-Regular.ttf", 24)
    f_meta_label = _font("Lora-Regular.ttf", 20)
    f_date_value = _font("Lora-Bold.ttf", 20)
    f_signature = _font("NothingYouCouldDo-Regular.ttf", 42)

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

    # --- Nishon (medal) - "TAQDIM ETILADI" yozuvi tepasida ---
    medal_r = 88
    medal_cx, medal_cy = margin_x + medal_r - 10, 300
    _draw_medal(draw, medal_cx, medal_cy, medal_r)

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
        draw.text((content_x, sig_y - 54), signature_name, font=f_signature, fill=NAVY2)
        draw.line([(content_x, sig_y), (content_x + sig_w, sig_y)], fill=LINE_GRAY, width=1)
        draw.text((content_x, sig_y + 12), "Loyiha muallifi", font=f_meta_label, fill=GRAY)

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
