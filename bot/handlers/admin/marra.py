from datetime import date, timedelta

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_MARRA,
    CB_ADMIN_MARRA_PREVIEW,
    CB_ADMIN_MARRA_SET_DURATION,
    CB_ADMIN_MARRA_SET_HOUR,
    CB_ADMIN_MARRA_SET_TEXT,
    CB_ADMIN_MARRA_SET_URL,
    cancel_keyboard,
    marra_menu_keyboard,
)
from bot.keyboards.user import marra_keyboard
from bot.models.user import User
from bot.repositories.settings_repo import SettingsRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import MarraStates

router = Router(name="admin_marra")

DEFAULT_MARRA_REMINDER_TEXT = "📖 Bugungi Marra vazifangizni bajarishni unutmang!"


async def _menu_text(session: AsyncSession, settings) -> str:
    result = await session.execute(
        select(func.count()).select_from(User).where(User.is_marra_participant.is_(True))
    )
    participant_count = result.scalar_one()

    if settings.marra_end_date:
        days_left = (settings.marra_end_date - date.today()).days
        if days_left >= 0:
            duration_line = f"{settings.marra_end_date.strftime('%d.%m.%Y')} gacha ({days_left} kun qoldi)"
        else:
            duration_line = f"{settings.marra_end_date.strftime('%d.%m.%Y')} da tugagan (eslatma to'xtagan)"
    else:
        duration_line = "cheklanmagan (doimiy yuboriladi)"

    return (
        "📖 Marra (Mutolaa kitob o'qish challenge'i):\n\n"
        f"Havola: {settings.marra_url or '(sozlanmagan)'}\n"
        f"Eslatma matni: {settings.marra_reminder_text or DEFAULT_MARRA_REMINDER_TEXT}\n"
        f"Eslatma soati: {settings.marra_reminder_hour:02d}:00 (Asia/Tashkent)\n"
        f"Eslatma muddati: {duration_line}\n"
        f"Ishtirokchilar: {participant_count} kishi\n\n"
        "Diqqat: bot Mutolaa ilovasidan foydalanuvchining real o'qish holatini "
        "(daqiqasi, chetlatilgan-chetlatilmaganini) avtomatik bila olmaydi - "
        "chunki bu boshqa ilova va API'si yo'q. Bot faqat havolani ochib beradi "
        "va o'zi 'qo'shilaman' degan foydalanuvchilarga kunlik eslatma yuboradi."
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_MARRA)
async def on_marra_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    await callback.message.edit_text(await _menu_text(session, settings), reply_markup=marra_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_MARRA_PREVIEW)
async def on_preview(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    if not settings.marra_url:
        await callback.answer("Avval havolani sozlang.", show_alert=True)
        return

    text = settings.marra_reminder_text or DEFAULT_MARRA_REMINDER_TEXT
    await callback.message.answer(
        "🔍 Foydalanuvchi aynan shu ko'rinishda ko'radi (eslatma xabari namunasi):",
    )
    await callback.message.answer(
        text, reply_markup=marra_keyboard(settings.marra_url, is_participant=True)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_MARRA_SET_URL)
async def on_set_url_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MarraStates.waiting_url)
    await callback.message.edit_text(
        "Marra sahifasining havolasini yuboring (masalan: https://mutolaa.com/davra/post/489229):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(MarraStates.waiting_url)
async def on_url_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    url = (message.text or "").strip()
    if not url.startswith("https://"):
        await message.answer("Havola https:// bilan boshlanishi kerak. Qaytadan yuboring.", reply_markup=cancel_keyboard())
        return

    settings = await SettingsRepo(session).get()
    settings.marra_url = url
    await log_admin_action(session, message.from_user.id, "set_marra_url", url)
    await session.commit()
    await state.clear()
    await message.answer(
        "Marra havolasi sozlandi.", reply_markup=marra_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_MARRA_SET_TEXT)
async def on_set_text_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    current = settings.marra_reminder_text or DEFAULT_MARRA_REMINDER_TEXT
    await state.set_state(MarraStates.waiting_reminder_text)
    await callback.message.edit_text(
        f"Joriy eslatma matni:\n\n{current}\n\nYangi matnni yuboring:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(MarraStates.waiting_reminder_text)
async def on_text_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.marra_reminder_text = message.text
    await log_admin_action(session, message.from_user.id, "set_marra_reminder_text")
    await session.commit()
    await state.clear()
    await message.answer("Eslatma matni yangilandi.", reply_markup=marra_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_MARRA_SET_HOUR)
async def on_set_hour_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MarraStates.waiting_reminder_hour)
    await callback.message.edit_text(
        "Eslatma har kuni necha soatda (0-23, Asia/Tashkent vaqti bo'yicha) "
        "yuborilishini kiriting (masalan: 20):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(MarraStates.waiting_reminder_hour)
async def on_hour_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not (0 <= int(text) <= 23):
        await message.answer("0 dan 23 gacha butun son kiriting.", reply_markup=cancel_keyboard())
        return

    settings = await SettingsRepo(session).get()
    settings.marra_reminder_hour = int(text)
    await log_admin_action(session, message.from_user.id, "set_marra_reminder_hour", text)
    await session.commit()
    await state.clear()
    await message.answer(
        f"Eslatma soati {int(text):02d}:00 ga o'zgartirildi.", reply_markup=marra_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_MARRA_SET_DURATION)
async def on_set_duration_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MarraStates.waiting_duration_days)
    await callback.message.edit_text(
        "Bugundan boshlab necha kun davomida kunlik eslatma yuborilsin? "
        "(masalan: 8). Cheklovni olib tashlash uchun 0 yuboring.",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(MarraStates.waiting_duration_days)
async def on_duration_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Musbat butun son kiriting (yoki cheklovsiz uchun 0).", reply_markup=cancel_keyboard())
        return

    days = int(text)
    settings = await SettingsRepo(session).get()

    if days == 0:
        settings.marra_end_date = None
        await log_admin_action(session, message.from_user.id, "clear_marra_end_date")
        confirm_text = "Eslatma muddati cheklovi olib tashlandi - endi doimiy yuboriladi."
    else:
        settings.marra_end_date = date.today() + timedelta(days=days)
        await log_admin_action(session, message.from_user.id, "set_marra_end_date", str(settings.marra_end_date))
        confirm_text = (
            f"Eslatma {days} kun davomida, ya'ni {settings.marra_end_date.strftime('%d.%m.%Y')} "
            "sanasigacha yuboriladi."
        )

    await session.commit()
    await state.clear()
    await message.answer(confirm_text, reply_markup=marra_menu_keyboard())
