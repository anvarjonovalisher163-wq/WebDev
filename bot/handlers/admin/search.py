from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import CB_ADMIN_SEARCH, cancel_keyboard, search_results_keyboard, user_detail_keyboard
from bot.models.referral import ReferralStatus
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.user_repo import UserRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import SearchStates

router = Router(name="admin_search")


async def _render_user_card(session: AsyncSession, user_id: int) -> tuple[str, object]:
    user_repo = UserRepo(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        return "Foydalanuvchi topilmadi.", None

    referral_repo = ReferralRepo(session)
    approved_count = await referral_repo.count_by_referrer_and_status(user.id, ReferralStatus.APPROVED)
    total_invited = await user_repo.count_referred_by(user.id)

    referrer_line = "-"
    if user.referrer_id is not None:
        referrer = await user_repo.get_by_id(user.referrer_id)
        if referrer is not None:
            referrer_line = f"{referrer.first_name} (ID: {referrer.tg_id})"

    text = (
        f"<b>{user.first_name} {user.last_name or ''}</b>\n"
        f"Telegram ID: <code>{user.tg_id}</code>\n"
        f"Username: @{user.username or '-'}\n"
        f"Ro'yxatdan o'tgan: {user.created_at:%Y-%m-%d %H:%M}\n"
        f"Kim tomonidan taklif qilingan: {referrer_line}\n"
        f"Nechta odam taklif qilgan: {total_invited}\n"
        f"Tasdiqlangan referral soni: {approved_count}\n"
        f"Majburiy kanallarga obuna: {'ha' if user.is_subscribed else 'yoʼq'}\n"
        f"Maxfiy havola olgan: {'ha' if user.secret_link_taken else 'yoʼq'}\n"
        f"Yopiq kanalga qo'shilgan: {'ha' if user.joined_private_channel else 'yoʼq'}\n"
        f"Holati: {'bloklangan' if user.is_blocked else 'faol'}"
    )
    return text, user


@router.callback_query(lambda c: c.data == CB_ADMIN_SEARCH)
async def on_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_query)
    await callback.message.edit_text(
        "Telegram ID, username yoki ism bo'yicha qidiring:", reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.message(SearchStates.waiting_query)
async def on_search_query_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    users = await UserRepo(session).search(message.text or "")
    await state.clear()
    if not users:
        await message.answer("Hech narsa topilmadi.", reply_markup=cancel_keyboard())
        return
    await message.answer("Natijalar:", reply_markup=search_results_keyboard(users))


@router.callback_query(lambda c: c.data.startswith("admin:user:"))
async def on_user_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    user_id = int(callback.data.split(":")[-1])
    text, user = await _render_user_card(session, user_id)
    if user is None:
        await callback.answer(text, show_alert=True)
        return
    await callback.message.edit_text(text, reply_markup=user_detail_keyboard(user))
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:user_toggle_block:"))
async def on_user_toggle_block(callback: CallbackQuery, session: AsyncSession) -> None:
    user_id = int(callback.data.split(":")[-1])
    user = await UserRepo(session).get_by_id(user_id)
    if user is None:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    user.is_blocked = not user.is_blocked
    await log_admin_action(
        session, callback.from_user.id, "toggle_block_user", f"{user.tg_id}:{user.is_blocked}"
    )
    await session.commit()
    await callback.answer("Holat o'zgartirildi")
    text, _ = await _render_user_card(session, user_id)
    await callback.message.edit_text(text, reply_markup=user_detail_keyboard(user))


@router.callback_query(lambda c: c.data.startswith("admin:user_message:"))
async def on_user_message_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = int(callback.data.split(":")[-1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(SearchStates.waiting_message_text)
    await callback.message.edit_text("Foydalanuvchiga yubormoqchi bo'lgan xabaringizni yozing:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(SearchStates.waiting_message_text)
async def on_user_message_received(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    data = await state.get_data()
    user = await UserRepo(session).get_by_id(data["target_user_id"])
    await state.clear()
    if user is None:
        await message.answer("Foydalanuvchi topilmadi.")
        return

    try:
        await bot.send_message(user.tg_id, message.html_text)
        await log_admin_action(session, message.from_user.id, "send_individual_message", str(user.tg_id))
        await session.commit()
        await message.answer("Xabar yuborildi.", reply_markup=user_detail_keyboard(user))
    except TelegramBadRequest:
        await message.answer("Xabarni yuborib bo'lmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).")
