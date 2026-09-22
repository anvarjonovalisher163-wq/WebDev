import asyncio
import smtplib
from email.mime.text import MIMEText

from loguru import logger

from bot.config import settings


def _send_sync(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_login_code_email(to_email: str, code: str) -> bool:
    """Kirish kodini emailga yuboradi. SMTP sozlanmagan yoki xatolik bo'lsa
    False qaytaradi - chaqiruvchi tomon buni foydalanuvchiga tushuntiradi."""
    if not settings.smtp_configured:
        return False

    subject = "UCHQUN - kirish kodi"
    body = f"Sizning UCHQUNga kirish kodingiz: {code}\n\nBu kod 10 daqiqa amal qiladi."
    try:
        await asyncio.to_thread(_send_sync, to_email, subject, body)
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.error(f"Email yuborib bo'lmadi ({to_email}): {exc}")
        return False
