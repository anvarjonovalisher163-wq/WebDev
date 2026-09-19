from typing import Union

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    CB_ADMIN_SECRET_CHANNEL,
    CB_ADMIN_SECRET_SET_CHANNEL,
    CB_ADMIN_SECRET_SET_LIMIT,
    CB_ADMIN_SECRET_SET_MAX_REISSUE,
    CB_ADMIN_SECRET_SET_TTL,
    CB_ADMIN_SECRET_TOGGLE_REISSUE,
    cancel_keyboard,
    secret_channel_menu_keyboard,
)
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.services.audit import log_admin_action
from bot.states.admin_states import SecretChannelStates

router = Router(name="admin_secret_channel")


def _normalize_identifier(raw: str) -> Union[str, int]:
    raw = raw.strip()
    if raw.startswith("https://t.me/"):
        raw = raw[len("https://t.me/"):]
    if raw.startswith("@"):
        return raw
    if raw.lstrip("-").isdigit():
        return int(raw)
    return f"@{raw}"


def _settings_text(settings, season) -> str:
    channel_line = season.secret_channel_title or "(sozlanmagan)"
    reissue_label = "yoqilgan" if settings.reissue_allowed else "o'chirilgan"
    return (
        f"Maxfiy kanal sozlamalari ({season.name}):\n\n"
        f"Kanal: {channel_line}\n"
        f"Amal qilish muddati: {settings.link_ttl_minutes} daqiqa\n"
        f"Foydalanish limiti: {settings.link_member_limit} kishi\n"
        f"Qayta havola olish: {reissue_label}\n"
        f"Maksimal qayta urinish: {settings.max_reissue_attempts} marta\n\n"
        "Diqqat: har bir mavsum o'z yopiq kanaliga ega - yangi mavsum "
        "boshlanganda kanalni qaytadan sozlash kerak bo'ladi."
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_SECRET_CHANNEL)
async def on_secret_channel_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    season = await SeasonRepo(session).get_active()
    await callback.message.edit_text(
        _settings_text(settings, season), reply_markup=secret_channel_menu_keyboard(settings.reissue_allowed)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_SECRET_SET_CHANNEL)
async def on_set_channel_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SecretChannelStates.waiting_identifier)
    await callback.message.edit_text(
        "Yopiq kanalning @username yoki chat ID raqamini yuboring.\n"
        "Bot bu kanalda administrator bo'lishi va foydalanuvchilarni taklif qilish huquqiga ega bo'lishi kerak.",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SecretChannelStates.waiting_identifier)
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

    can_invite = getattr(member, "can_invite_users", False)
    if member.status not in ("administrator", "creator") or not can_invite:
        await message.answer(
            "Bot ushbu kanalda administrator bo'lishi va \"foydalanuvchilarni taklif qilish\" "
            "huquqiga ega bo'lishi kerak. Sozlab, qayta yuboring.",
            reply_markup=cancel_keyboard(),
        )
        return

    settings = await SettingsRepo(session).get()
    season = await SeasonRepo(session).get_active()
    season.secret_channel_id = chat.id
    season.secret_channel_title = chat.title or chat.username or str(chat.id)
    await log_admin_action(session, message.from_user.id, "set_secret_channel", str(chat.id))
    await session.commit()
    await state.clear()
    await message.answer(
        f"Maxfiy kanal {season.name} uchun sozlandi.",
        reply_markup=secret_channel_menu_keyboard(settings.reissue_allowed),
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_SECRET_SET_TTL)
async def on_set_ttl_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SecretChannelStates.waiting_ttl)
    await callback.message.edit_text(
        "Havolaning amal qilish muddatini daqiqalarda yuboring (masalan: 30):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SecretChannelStates.waiting_ttl)
async def on_ttl_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Musbat butun son kiriting (daqiqada).", reply_markup=cancel_keyboard())
        return

    settings = await SettingsRepo(session).get()
    settings.link_ttl_minutes = int(text)
    await log_admin_action(session, message.from_user.id, "set_link_ttl", text)
    await session.commit()
    await state.clear()
    await message.answer(
        f"Amal qilish muddati {text} daqiqaga o'zgartirildi.",
        reply_markup=secret_channel_menu_keyboard(settings.reissue_allowed),
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_SECRET_SET_LIMIT)
async def on_set_limit_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SecretChannelStates.waiting_member_limit)
    await callback.message.edit_text(
        "Havolaning foydalanish limitini yuboring (odatda 1):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SecretChannelStates.waiting_member_limit)
async def on_limit_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Musbat butun son kiriting.", reply_markup=cancel_keyboard())
        return

    settings = await SettingsRepo(session).get()
    settings.link_member_limit = int(text)
    await log_admin_action(session, message.from_user.id, "set_link_member_limit", text)
    await session.commit()
    await state.clear()
    await message.answer(
        f"Foydalanish limiti {text} taga o'zgartirildi.",
        reply_markup=secret_channel_menu_keyboard(settings.reissue_allowed),
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_SECRET_TOGGLE_REISSUE)
async def on_toggle_reissue(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await SettingsRepo(session).get()
    settings.reissue_allowed = not settings.reissue_allowed
    await log_admin_action(session, callback.from_user.id, "toggle_reissue", str(settings.reissue_allowed))
    await session.commit()
    season = await SeasonRepo(session).get_active()
    await callback.answer("Sozlama o'zgartirildi")
    await callback.message.edit_text(
        _settings_text(settings, season), reply_markup=secret_channel_menu_keyboard(settings.reissue_allowed)
    )


@router.callback_query(lambda c: c.data == CB_ADMIN_SECRET_SET_MAX_REISSUE)
async def on_set_max_reissue_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SecretChannelStates.waiting_max_reissue)
    await callback.message.edit_text(
        "Bitta foydalanuvchi necha marta yangi havola olishi mumkinligini yuboring:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SecretChannelStates.waiting_max_reissue)
async def on_max_reissue_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Musbat butun son kiriting.", reply_markup=cancel_keyboard())
        return

    settings = await SettingsRepo(session).get()
    settings.max_reissue_attempts = int(text)
    await log_admin_action(session, message.from_user.id, "set_max_reissue", text)
    await session.commit()
    await state.clear()
    await message.answer(
        f"Maksimal qayta urinish soni {text} taga o'zgartirildi.",
        reply_markup=secret_channel_menu_keyboard(settings.reissue_allowed),
    )
