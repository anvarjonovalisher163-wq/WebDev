from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram import Router
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import CB_ADMIN_REQUIREMENTS, back_to_admin_menu_keyboard, cancel_keyboard
from bot.repositories.settings_repo import SettingsRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import RequirementsStates

router = Router(name="admin_requirements")


@router.callback_query(lambda c: c.data == CB_ADMIN_REQUIREMENTS)
async def on_requirements_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    await state.set_state(RequirementsStates.waiting_count)
    await callback.message.edit_text(
        f"Joriy talab: {settings.required_referral_count} ta tasdiqlangan referral.\n\n"
        "Yangi qiymatni butun son sifatida yuboring:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(RequirementsStates.waiting_count)
async def on_requirements_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, musbat butun son kiriting (masalan: 5).", reply_markup=cancel_keyboard())
        return

    settings = await SettingsRepo(session).get()
    settings.required_referral_count = int(text)
    await log_admin_action(session, message.from_user.id, "update_requirements", text)
    await session.commit()
    await state.clear()
    await message.answer(
        f"Talab qilinadigan referral soni {text} taga o'zgartirildi.",
        reply_markup=back_to_admin_menu_keyboard(),
    )
