from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.admin import CB_ADMIN_BACK, CB_ADMIN_CANCEL, admin_main_menu_keyboard

router = Router(name="admin_panel")

ADMIN_MENU_TEXT = "Admin panel:"


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_MENU_TEXT, reply_markup=admin_main_menu_keyboard())


@router.callback_query(lambda c: c.data == CB_ADMIN_BACK)
async def on_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(ADMIN_MENU_TEXT, reply_markup=admin_main_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_CANCEL)
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(ADMIN_MENU_TEXT, reply_markup=admin_main_menu_keyboard())
    await callback.answer("Bekor qilindi")
