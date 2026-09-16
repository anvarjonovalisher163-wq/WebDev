from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_REFERRAL_IMAGE,
    CB_ADMIN_REFERRAL_IMAGE_REMOVE,
    CB_ADMIN_REFERRAL_PREVIEW,
    CB_ADMIN_REFERRAL_TEXT,
    CB_ADMIN_SHARE_TEXT,
    back_to_admin_menu_keyboard,
    cancel_keyboard,
    referral_content_menu_keyboard,
)
from bot.keyboards.user import DEFAULT_SHARE_TEXT
from bot.repositories.settings_repo import SettingsRepo
from bot.services.audit import log_admin_action
from bot.services.user_service import build_referral_link
from bot.states.admin_states import ReferralContentStates

router = Router(name="admin_referral_content")

DEFAULT_REFERRAL_TEXT = "Yopiq kanalga qo'shilish uchun botga kiring: {referral_link}"


@router.callback_query(lambda c: c.data == CB_ADMIN_REFERRAL_TEXT)
async def on_referral_text_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReferralContentStates.waiting_text)
    await callback.message.edit_text(
        "Yangi referral post matnini yuboring.\n"
        "Foydalanuvchining unikal havolasi uchun {referral_link} o'zgaruvchisidan foydalaning.",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(ReferralContentStates.waiting_text)
async def on_referral_text_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.referral_text = message.html_text
    await log_admin_action(session, message.from_user.id, "update_referral_text")
    await session.commit()
    await state.clear()
    await message.answer("Referral matni yangilandi.", reply_markup=referral_content_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_REFERRAL_IMAGE)
async def on_referral_image_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReferralContentStates.waiting_image)
    await callback.message.edit_text("Referral post uchun rasm yuboring:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ReferralContentStates.waiting_image, F.photo)
async def on_referral_image_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.referral_image_file_id = message.photo[-1].file_id
    await log_admin_action(session, message.from_user.id, "update_referral_image")
    await session.commit()
    await state.clear()
    await message.answer("Referral rasmi saqlandi.", reply_markup=referral_content_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_REFERRAL_IMAGE_REMOVE)
async def on_referral_image_remove(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.referral_image_file_id = None
    await log_admin_action(session, callback.from_user.id, "remove_referral_image")
    await session.commit()
    await callback.answer("Rasm olib tashlandi")
    await callback.message.edit_text(
        "Referral kontenti sozlamalari:", reply_markup=referral_content_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_SHARE_TEXT)
async def on_share_text_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    current = settings.share_text or DEFAULT_SHARE_TEXT
    await state.set_state(ReferralContentStates.waiting_share_text)
    await callback.message.edit_text(
        f"Joriy Ulashish matni:\n\n{current}\n\n"
        "Bu matn foydalanuvchi \"Ulashish\" tugmasini bosganda Telegram'ning forward "
        "oynasida ko'rinadi. Yangi matnni yuboring:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(ReferralContentStates.waiting_share_text)
async def on_share_text_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.share_text = message.text
    await log_admin_action(session, message.from_user.id, "update_share_text")
    await session.commit()
    await state.clear()
    await message.answer("Ulashish matni yangilandi.", reply_markup=back_to_admin_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_REFERRAL_PREVIEW)
async def on_referral_preview(callback: CallbackQuery, session: AsyncSession, bot_username: str) -> None:
    settings = await SettingsRepo(session).get()
    template = settings.referral_text or DEFAULT_REFERRAL_TEXT
    sample_link = build_referral_link(bot_username, callback.from_user.id)
    text = template.replace("{referral_link}", sample_link)

    if settings.referral_image_file_id:
        await callback.message.answer_photo(settings.referral_image_file_id, caption=text)
    else:
        await callback.message.answer(text)
    await callback.answer()
