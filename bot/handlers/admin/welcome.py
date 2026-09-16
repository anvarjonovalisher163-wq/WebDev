from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_WELCOME,
    CB_ADMIN_WELCOME_MEDIA,
    CB_ADMIN_WELCOME_MEDIA_REMOVE,
    CB_ADMIN_WELCOME_TEXT,
    cancel_keyboard,
    welcome_menu_keyboard,
)
from bot.repositories.settings_repo import SettingsRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import WelcomeStates

router = Router(name="admin_welcome")


@router.callback_query(lambda c: c.data == CB_ADMIN_WELCOME)
async def on_welcome_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    preview = settings.welcome_text or "(hali kiritilmagan)"
    await callback.message.edit_text(
        f"Joriy Welcome matni:\n\n{preview}",
        reply_markup=welcome_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_WELCOME_TEXT)
async def on_welcome_text_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WelcomeStates.waiting_text)
    await callback.message.edit_text(
        "Yangi Welcome matnini yuboring (HTML formatlash: &lt;b&gt;, &lt;i&gt;, havolalar mumkin).\n"
        "Foydalanuvchining ismini avtomatik joylashtirish uchun {ism} o'zgaruvchisidan foydalaning.\n\n"
        "Masalan: \"Assalomu alaykum, {ism}! Botga xush kelibsiz.\"",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(WelcomeStates.waiting_text)
async def on_welcome_text_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.welcome_text = message.html_text
    await log_admin_action(session, message.from_user.id, "update_welcome_text")
    await session.commit()
    await state.clear()
    await message.answer("Welcome matni yangilandi.", reply_markup=welcome_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_WELCOME_MEDIA)
async def on_welcome_media_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WelcomeStates.waiting_media)
    await callback.message.edit_text("Rasm yoki video yuboring:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(WelcomeStates.waiting_media, F.photo)
async def on_welcome_media_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.welcome_media_file_id = message.photo[-1].file_id
    settings.welcome_media_type = "photo"
    await log_admin_action(session, message.from_user.id, "update_welcome_media", "photo")
    await session.commit()
    await state.clear()
    await message.answer("Welcome rasmi saqlandi.", reply_markup=welcome_menu_keyboard())


@router.message(WelcomeStates.waiting_media, F.video)
async def on_welcome_media_video(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.welcome_media_file_id = message.video.file_id
    settings.welcome_media_type = "video"
    await log_admin_action(session, message.from_user.id, "update_welcome_media", "video")
    await session.commit()
    await state.clear()
    await message.answer("Welcome video saqlandi.", reply_markup=welcome_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_WELCOME_MEDIA_REMOVE)
async def on_welcome_media_remove(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.welcome_media_file_id = None
    settings.welcome_media_type = None
    await log_admin_action(session, callback.from_user.id, "remove_welcome_media")
    await session.commit()
    await callback.answer("Media olib tashlandi")
    await callback.message.edit_text(
        f"Joriy Welcome matni:\n\n{settings.welcome_text or '(hali kiritilmagan)'}",
        reply_markup=welcome_menu_keyboard(),
    )
