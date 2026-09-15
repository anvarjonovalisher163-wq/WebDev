from typing import Union

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_CHANNEL_ADD,
    CB_ADMIN_CHANNELS,
    cancel_keyboard,
    channel_detail_keyboard,
    channels_list_keyboard,
)
from bot.repositories.channel_repo import ChannelRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import ChannelStates

router = Router(name="admin_channels")


def _normalize_identifier(raw: str) -> Union[str, int]:
    raw = raw.strip()
    if raw.startswith("https://t.me/"):
        raw = raw[len("https://t.me/"):]
    if raw.startswith("@"):
        return raw
    if raw.lstrip("-").isdigit():
        return int(raw)
    return f"@{raw}"


@router.callback_query(lambda c: c.data == CB_ADMIN_CHANNELS)
async def on_channels_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    channels = await ChannelRepo(session).list_all()
    text = "Majburiy kanallar:" if channels else "Hozircha majburiy kanallar qo'shilmagan."
    await callback.message.edit_text(text, reply_markup=channels_list_keyboard(channels))
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_CHANNEL_ADD)
async def on_channel_add_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ChannelStates.waiting_identifier)
    await callback.message.edit_text(
        "Kanalning @username yoki chat ID raqamini yuboring.\n"
        "Bot avvaldan ushbu kanalga administrator etib qo'shilgan bo'lishi kerak.",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(ChannelStates.waiting_identifier)
async def on_channel_identifier_received(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    identifier = _normalize_identifier(message.text or "")
    try:
        chat = await bot.get_chat(identifier)
        member = await bot.get_chat_member(chat.id, bot.id)
    except TelegramBadRequest:
        await message.answer(
            "Kanal topilmadi yoki bot u yerga qo'shilmagan. Qaytadan urinib ko'ring.",
            reply_markup=cancel_keyboard(),
        )
        return

    if member.status not in ("administrator", "creator"):
        await message.answer(
            "Bot ushbu kanalda administrator emas. Avval botni admin qiling, so'ng qayta yuboring.",
            reply_markup=cancel_keyboard(),
        )
        return

    channel_repo = ChannelRepo(session)
    await channel_repo.add(
        title=chat.title or chat.username or str(chat.id),
        chat_id=chat.id,
        username=chat.username,
        invite_url=f"https://t.me/{chat.username}" if chat.username else chat.invite_link,
    )
    await log_admin_action(session, message.from_user.id, "add_channel", str(chat.id))
    await session.commit()
    await state.clear()

    channels = await channel_repo.list_all()
    await message.answer("Kanal qo'shildi.", reply_markup=channels_list_keyboard(channels))


@router.callback_query(lambda c: c.data.startswith("admin:channel:"))
async def on_channel_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    channel_id = int(callback.data.split(":")[-1])
    channel = await ChannelRepo(session).get_by_id(channel_id)
    if channel is None:
        await callback.answer("Kanal topilmadi", show_alert=True)
        return
    status = "faol" if channel.is_active else "faol emas"
    text = (
        f"<b>{channel.title}</b>\n"
        f"Chat ID: <code>{channel.chat_id}</code>\n"
        f"Username: {channel.username or '-'}\n"
        f"Holati: {status}"
    )
    await callback.message.edit_text(text, reply_markup=channel_detail_keyboard(channel))
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:channel_toggle:"))
async def on_channel_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    channel_id = int(callback.data.split(":")[-1])
    channel_repo = ChannelRepo(session)
    channel = await channel_repo.get_by_id(channel_id)
    if channel is None:
        await callback.answer("Kanal topilmadi", show_alert=True)
        return
    channel.is_active = not channel.is_active
    await log_admin_action(session, callback.from_user.id, "toggle_channel", str(channel.chat_id))
    await session.commit()
    await callback.answer("Holat o'zgartirildi")
    await callback.message.edit_reply_markup(reply_markup=channel_detail_keyboard(channel))


@router.callback_query(lambda c: c.data.startswith("admin:channel_del:"))
async def on_channel_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    channel_id = int(callback.data.split(":")[-1])
    channel_repo = ChannelRepo(session)
    channel = await channel_repo.get_by_id(channel_id)
    if channel is None:
        await callback.answer("Kanal topilmadi", show_alert=True)
        return

    chat_id = channel.chat_id
    await channel_repo.delete(channel)
    await log_admin_action(session, callback.from_user.id, "delete_channel", str(chat_id))
    await session.commit()

    channels = await channel_repo.list_all()
    await callback.answer("Kanal o'chirildi")
    await callback.message.edit_text(
        "Majburiy kanallar:" if channels else "Hozircha majburiy kanallar qo'shilmagan.",
        reply_markup=channels_list_keyboard(channels),
    )
