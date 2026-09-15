from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_BROADCAST,
    CB_ADMIN_BROADCAST_CONFIRM,
    admin_main_menu_keyboard,
    broadcast_confirm_keyboard,
    cancel_keyboard,
)
from bot.services.audit import log_admin_action
from bot.services.broadcast_service import BroadcastService
from bot.states.admin_states import BroadcastStates

router = Router(name="admin_broadcast")


@router.callback_query(lambda c: c.data == CB_ADMIN_BROADCAST)
async def on_broadcast_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_content)
    await callback.message.edit_text(
        "Yubormoqchi bo'lgan xabarni yuboring (matn, rasm, video, hujjat, audio yoki forward):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_content, F.text | F.photo | F.video | F.document | F.audio)
async def on_broadcast_content_received(message: Message, state: FSMContext) -> None:
    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastStates.waiting_confirmation)
    await message.reply(
        "Yuqoridagi xabar barcha foydalanuvchilarga shu ko'rinishda yuboriladi. Tasdiqlaysizmi?",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(BroadcastStates.waiting_confirmation, lambda c: c.data == CB_ADMIN_BROADCAST_CONFIRM)
async def on_broadcast_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    data = await state.get_data()
    await state.clear()
    await callback.answer("Yuborish boshlandi, biroz vaqt olishi mumkin...")
    await callback.message.edit_reply_markup(reply_markup=None)

    broadcast_service = BroadcastService(session, bot)
    report = await broadcast_service.send_to_all(data["from_chat_id"], data["message_id"])

    await log_admin_action(
        session,
        callback.from_user.id,
        "broadcast",
        f"total={report.total} success={report.success} blocked={report.blocked} failed={report.failed}",
    )
    await session.commit()

    await callback.message.answer(
        "E'lon yuborish yakunlandi.\n\n"
        f"Jami foydalanuvchilar: {report.total}\n"
        f"Muvaffaqiyatli yuborildi: {report.success}\n"
        f"Botni bloklaganlar: {report.blocked}\n"
        f"Xatolik yuz berganlar: {report.failed}",
        reply_markup=admin_main_menu_keyboard(),
    )
