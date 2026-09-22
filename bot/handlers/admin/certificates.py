import asyncio
from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_CERT_ROSTER,
    CB_ADMIN_CERT_ROSTER_CONFIRM,
    CB_ADMIN_CERTIFICATES,
    cancel_keyboard,
    cert_roster_confirm_keyboard,
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
from bot.states.admin_states import CertRosterStates
from bot.states.user_states import CertificateStates

router = Router(name="admin_certificates")

DEFAULT_CERT_ROSTER_TEXT = "🎓 Sertifikatingizni olish uchun ismingizni kiriting:"

_THROTTLE_SECONDS = 0.05


async def _stats_text(session: AsyncSession) -> str:
    user_repo = UserRepo(session)
    joined = await user_repo.count_joined_private_channel()
    filled = await user_repo.count_cert_form_filled()
    issued = await user_repo.count_cert_issued()
    pending = filled - issued

    return (
        "🎓 Sertifikatlar:\n\n"
        f"Yopiq kanalga qo'shilganlar: {joined}\n"
        f"Forma to'ldirganlar: {filled}\n"
        f"Sertifikat berilganlar: {issued}\n"
        f"Admin tasdig'ini kutayotganlar: {pending}"
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_CERTIFICATES)
async def on_certificates_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.message.edit_text(await _stats_text(session), reply_markup=certificates_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_CERT_ROSTER)
async def on_cert_roster_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CertRosterStates.waiting_message_text)
    await callback.message.edit_text(
        "Yopiq kanaldagi barcha ishtirokchilarga yuboriladigan xabar matnini yuboring "
        "(xohlasangiz tahrirlab, xohlasangiz shu matnni xuddi shunday nusxalab yuboring):\n\n"
        f"{DEFAULT_CERT_ROSTER_TEXT}",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(CertRosterStates.waiting_message_text, F.text)
async def on_cert_roster_text_received(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    text = message.text.strip()
    await state.update_data(roster_text=text)
    await state.set_state(CertRosterStates.waiting_confirmation)

    count = len(await UserRepo(session).list_joined_private_channel_not_blocked())
    await message.answer(
        f"Quyidagi matn {count} ta ishtirokchiga yuboriladi, shundan so'ng bot ulardan "
        "ism va familiyasini alohida so'raydi:\n\n"
        f"{text}\n\nTasdiqlaysizmi?",
        reply_markup=cert_roster_confirm_keyboard(),
    )


@router.message(CertRosterStates.waiting_message_text)
async def on_cert_roster_text_invalid(message: Message) -> None:
    await message.answer("Iltimos, xabar matnini oddiy matn ko'rinishida yuboring:")


@router.callback_query(CertRosterStates.waiting_confirmation, lambda c: c.data == CB_ADMIN_CERT_ROSTER_CONFIRM)
async def on_cert_roster_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    data = await state.get_data()
    roster_text = data.get("roster_text") or DEFAULT_CERT_ROSTER_TEXT
    await state.clear()
    await callback.answer("Yuborish boshlandi...")
    await callback.message.edit_text("⏳ Xabarlar yuborilmoqda...")

    users = await UserRepo(session).list_joined_private_channel_not_blocked()
    sent, failed = 0, 0

    for user in users:
        try:
            await bot.send_message(user.tg_id, roster_text)
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
            continue

        private_key = StorageKey(bot_id=bot.id, chat_id=user.tg_id, user_id=user.tg_id)
        await FSMContext(storage=state.storage, key=private_key).set_state(
            CertificateStates.waiting_first_name
        )
        sent += 1
        await asyncio.sleep(_THROTTLE_SECONDS)

    await log_admin_action(
        session, callback.from_user.id, "cert_roster_broadcast", f"sent={sent} failed={failed}"
    )
    await session.commit()

    await callback.message.answer(
        f"✅ {sent} ta ishtirokchiga yuborildi.\n" + (f"⚠️ {failed} ta yuborilmadi.\n" if failed else "")
    )
    await callback.message.answer(await _stats_text(session), reply_markup=certificates_menu_keyboard())


async def _render_and_send_certificate(session: AsyncSession, bot: Bot, user) -> bool:
    settings = await SettingsRepo(session).get()
    season = await SeasonRepo(session).get_active()
    season_name = season.name if season else ""

    subtitle = settings.certificate_subtitle or DEFAULT_CERTIFICATE_SUBTITLE
    body_text = (settings.certificate_body_text or DEFAULT_CERTIFICATE_BODY_TEXT).replace(
        "{mavsum}", season_name
    )
    signature_name = settings.certificate_signature_name or DEFAULT_CERTIFICATE_SIGNATURE_NAME

    png = render_certificate_png(
        user.cert_full_name, subtitle, body_text, signature_name, datetime.now(timezone.utc).date()
    )
    try:
        await bot.send_document(
            user.tg_id,
            BufferedInputFile(png, filename="uchqun_sertifikat.png"),
            caption="🎓 Tabriklaymiz! Sizning UCHQUN loyihasidagi ishtirok sertifikatingiz.",
        )
    except (TelegramForbiddenError, TelegramBadRequest):
        return False
    return True


@router.callback_query(lambda c: c.data.startswith("admin:cert_approve:"))
async def on_cert_approve(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    user_id = int(callback.data.split(":")[-1])
    user = await UserRepo(session).get_by_id(user_id)
    if user is None or user.cert_full_name is None:
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    if user.cert_issued_at is not None:
        await callback.answer("Bu foydalanuvchiga sertifikat allaqachon yuborilgan.", show_alert=True)
        return

    sent = await _render_and_send_certificate(session, bot, user)
    if not sent:
        await callback.answer("Foydalanuvchiga yuborib bo'lmadi (bot bloklangan bo'lishi mumkin).", show_alert=True)
        return

    user.cert_issued_at = datetime.now(timezone.utc)
    await log_admin_action(session, callback.from_user.id, "approve_certificate", user.cert_full_name)
    await session.commit()

    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ Tasdiqlandi va sertifikat yuborildi.", reply_markup=None
    )
    await callback.answer("Yuborildi ✅")


@router.callback_query(lambda c: c.data.startswith("admin:cert_reject:"))
async def on_cert_reject(
    callback: CallbackQuery, session: AsyncSession, bot: Bot, state: FSMContext
) -> None:
    user_id = int(callback.data.split(":")[-1])
    user = await UserRepo(session).get_by_id(user_id)
    if user is None or user.cert_full_name is None:
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    rejected_name = user.cert_full_name
    user.cert_full_name = None
    user.cert_requested_at = None
    await log_admin_action(session, callback.from_user.id, "reject_certificate", rejected_name)
    await session.commit()

    try:
        await bot.send_message(
            user.tg_id,
            "❗️ Kiritgan ism-familiyangiz qabul qilinmadi. Iltimos, ismingizni qaytadan yuboring:",
        )
        private_key = StorageKey(bot_id=bot.id, chat_id=user.tg_id, user_id=user.tg_id)
        await FSMContext(storage=state.storage, key=private_key).set_state(
            CertificateStates.waiting_first_name
        )
    except (TelegramForbiddenError, TelegramBadRequest):
        pass

    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ Rad etildi ({rejected_name}).", reply_markup=None
    )
    await callback.answer("Rad etildi")
