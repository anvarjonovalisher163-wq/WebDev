from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_ADMIN_ADD,
    CB_ADMIN_ADMINS,
    admins_list_keyboard,
    cancel_keyboard,
)
from bot.models.admin import Admin
from bot.repositories.admin_repo import AdminRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import AdminManageStates

router = Router(name="admin_admins")


@router.callback_query(lambda c: c.data == CB_ADMIN_ADMINS)
async def on_admins_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    admin_repo = AdminRepo(session)
    admins = await admin_repo.list_all()
    current = await admin_repo.get_by_tg_id(callback.from_user.id)
    can_manage = current is not None and current.is_super_admin

    await callback.message.edit_text(
        "Adminlar ro'yxati:" if can_manage else "Adminlar ro'yxati (faqat bosh admin boshqara oladi):",
        reply_markup=admins_list_keyboard(admins, can_manage),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_ADMIN_ADD)
async def on_admin_add_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    current = await AdminRepo(session).get_by_tg_id(callback.from_user.id)
    if current is None or not current.is_super_admin:
        await callback.answer("Bu amal faqat bosh administratorlar uchun.", show_alert=True)
        return

    await state.set_state(AdminManageStates.waiting_new_admin_id)
    await callback.message.edit_text(
        "Yangi adminning Telegram ID raqamini yuboring:", reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminManageStates.waiting_new_admin_id)
async def on_admin_id_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Iltimos, faqat raqamlardan iborat Telegram ID yuboring.", reply_markup=cancel_keyboard())
        return

    tg_id = int(text)
    admin_repo = AdminRepo(session)
    existing = await admin_repo.get_by_tg_id(tg_id)
    if existing is not None:
        await message.answer("Bu foydalanuvchi allaqachon admin.", reply_markup=cancel_keyboard())
        return

    await admin_repo.add(tg_id, is_super_admin=False, added_by=message.from_user.id)
    await log_admin_action(session, message.from_user.id, "add_admin", str(tg_id))
    await session.commit()
    await state.clear()

    admins = await admin_repo.list_all()
    await message.answer("Admin qo'shildi.", reply_markup=admins_list_keyboard(admins, can_manage=True))


@router.callback_query(lambda c: c.data.startswith("admin:admin_del:"))
async def on_admin_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    admin_repo = AdminRepo(session)
    current = await admin_repo.get_by_tg_id(callback.from_user.id)
    if current is None or not current.is_super_admin:
        await callback.answer("Bu amal faqat bosh administratorlar uchun.", show_alert=True)
        return

    admin_id = int(callback.data.split(":")[-1])
    target = await session.get(Admin, admin_id)
    if target is None:
        await callback.answer("Admin topilmadi", show_alert=True)
        return
    if target.is_super_admin:
        await callback.answer("Bosh adminni o'chirib bo'lmaydi.", show_alert=True)
        return

    tg_id = target.tg_id
    await admin_repo.remove(target)
    await log_admin_action(session, callback.from_user.id, "remove_admin", str(tg_id))
    await session.commit()

    admins = await admin_repo.list_all()
    await callback.answer("Admin o'chirildi")
    await callback.message.edit_text(
        "Adminlar ro'yxati:", reply_markup=admins_list_keyboard(admins, can_manage=True)
    )


@router.callback_query(lambda c: c.data.startswith("admin:noop:"))
async def on_admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()
