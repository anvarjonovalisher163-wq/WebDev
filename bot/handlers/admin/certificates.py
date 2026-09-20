from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_CERT_ISSUE_CONFIRM,
    CB_ADMIN_CERT_ISSUE_PROMPT,
    CB_ADMIN_CERTIFICATES,
    certificates_issue_confirm_keyboard,
    certificates_menu_keyboard,
)
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo
from bot.services.audit import log_admin_action
from bot.services.certificate_service import (
    DEFAULT_CERTIFICATE_BODY_TEXT,
    DEFAULT_CERTIFICATE_SIGNATURE_NAME,
    DEFAULT_CERTIFICATE_SUBTITLE,
    render_certificate_png,
)

router = Router(name="admin_certificates")


async def _stats_text(session: AsyncSession) -> tuple[str, int]:
    user_repo = UserRepo(session)
    joined = await user_repo.count_joined_private_channel()
    filled = await user_repo.count_cert_form_filled()
    issued = await user_repo.count_cert_issued()
    ready = filled - issued

    text = (
        "🎓 Sertifikatlar:\n\n"
        f"Yopiq kanalga qo'shilganlar: {joined}\n"
        f"Forma to'ldirganlar: {filled}\n"
        f"Sertifikat berilganlar: {issued}\n"
        f"Berishga tayyor: {ready}"
    )
    return text, ready


@router.callback_query(lambda c: c.data == CB_ADMIN_CERTIFICATES)
async def on_certificates_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    text, ready = await _stats_text(session)
    await callback.message.edit_text(text, reply_markup=certificates_menu_keyboard(ready))
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_CERT_ISSUE_PROMPT)
async def on_issue_prompt(callback: CallbackQuery, session: AsyncSession) -> None:
    _, ready = await _stats_text(session)
    await callback.message.edit_text(
        f"{ready} ta foydalanuvchiga sertifikat yuboriladi. Davom etasizmi?",
        reply_markup=certificates_issue_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_CERT_ISSUE_CONFIRM)
async def on_issue_confirm(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await callback.answer("Boshlandi...")
    await callback.message.edit_text("⏳ Sertifikatlar yuborilmoqda...")

    settings = await SettingsRepo(session).get()
    season = await SeasonRepo(session).get_active()
    season_name = season.name if season else ""

    subtitle = settings.certificate_subtitle or DEFAULT_CERTIFICATE_SUBTITLE
    body_text = (settings.certificate_body_text or DEFAULT_CERTIFICATE_BODY_TEXT).replace(
        "{mavsum}", season_name
    )
    signature_name = settings.certificate_signature_name or DEFAULT_CERTIFICATE_SIGNATURE_NAME

    users = await UserRepo(session).list_ready_for_certificate()
    sent, failed = 0, 0
    issued_date = datetime.now(timezone.utc).date()

    for user in users:
        png = render_certificate_png(user.cert_full_name, subtitle, body_text, signature_name, issued_date)
        try:
            await bot.send_document(
                user.tg_id,
                BufferedInputFile(png, filename="uchqun_sertifikat.png"),
                caption="🎓 Tabriklaymiz! Sizning UCHQUN loyihasidagi ishtirok sertifikatingiz.",
            )
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
            continue

        user.cert_issued_at = datetime.now(timezone.utc)
        sent += 1
        await session.commit()

    await log_admin_action(session, callback.from_user.id, "issue_certificates", f"sent={sent} failed={failed}")
    await session.commit()

    text, ready = await _stats_text(session)
    await callback.message.answer(
        f"✅ {sent} ta sertifikat yuborildi.\n" + (f"⚠️ {failed} ta yuborilmadi (bot bloklangan).\n" if failed else "")
    )
    await callback.message.answer(text, reply_markup=certificates_menu_keyboard(ready))
