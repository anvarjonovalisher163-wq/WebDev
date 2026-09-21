from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.filters.is_operator import IsOperator
from spam_bot.keyboards.groups import CB_GROUPS_BACK, group_detail_keyboard, groups_list_keyboard
from spam_bot.models.group import Group
from spam_bot.repositories.group_repo import GroupRepo

router = Router(name="admin_groups")


def _status_label(group: Group) -> str:
    if not group.enabled:
        return "⛔ o'chirilgan"
    if group.access_until is None:
        return "♾️ cheksiz bepul"
    now = datetime.now(timezone.utc)
    if group.access_until > now:
        return f"✅ obunali/sinov ({group.access_until.strftime('%Y-%m-%d')} gacha)"
    return "⏳ muddati o'tgan"


def _list_text(groups: list[Group]) -> str:
    if not groups:
        return "Hozircha botni hech qanday guruh admin qilib tayinlamagan."
    return f"📋 <b>Guruhlar</b> ({len(groups)} ta) — tafsilot uchun birini tanlang:"


async def _detail_text(bot, group: Group) -> str:
    link: str | None = None
    try:
        link = await bot.export_chat_invite_link(group.chat_id)
    except TelegramBadRequest:
        link = None

    gemini_label = "✅ bor" if group.gemini_key_encrypted else "❌ yo'q"
    link_label = link or "(olinmadi - botda 'foydalanuvchilarni taklif qilish' huquqi yo'q bo'lishi mumkin)"

    lines = [
        f"📌 <b>{group.title or group.chat_id}</b>",
        f"Chat ID: <code>{group.chat_id}</code>",
        f"Egasi (Telegram ID): <code>{group.owner_id}</code>",
        f"Holati: {_status_label(group)}",
        f"Gemini kaliti: {gemini_label}",
        f"Qo'shilgan sana: {group.created_at.strftime('%Y-%m-%d')}",
        f"Havola: {link_label}",
    ]
    return "\n".join(lines)


@router.message(Command("guruhlar"), F.chat.type == "private", IsOperator())
async def cmd_groups(message: Message, session: AsyncSession) -> None:
    groups = await GroupRepo(session).list_all()
    await message.answer(_list_text(groups), reply_markup=groups_list_keyboard(groups))


@router.callback_query(F.data == CB_GROUPS_BACK, IsOperator())
async def on_back(callback: CallbackQuery, session: AsyncSession) -> None:
    groups = await GroupRepo(session).list_all()
    await callback.message.edit_text(_list_text(groups), reply_markup=groups_list_keyboard(groups))
    await callback.answer()


@router.callback_query(F.data.startswith("group:"), IsOperator())
async def on_group_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    chat_id = int(callback.data.split(":", 1)[1])
    group = await GroupRepo(session).get_by_chat_id(chat_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    text = await _detail_text(callback.bot, group)
    await callback.message.edit_text(text, reply_markup=group_detail_keyboard(group))
    await callback.answer()


@router.callback_query(F.data.startswith("group_free:"), IsOperator())
async def on_mark_free(callback: CallbackQuery, session: AsyncSession) -> None:
    chat_id = int(callback.data.split(":", 1)[1])
    repo = GroupRepo(session)
    group = await repo.get_by_chat_id(chat_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    await repo.set_unlimited_free(group)
    await session.commit()

    text = await _detail_text(callback.bot, group)
    await callback.message.edit_text(text, reply_markup=group_detail_keyboard(group))
    await callback.answer("Cheksiz bepul qilib belgilandi ✅")


@router.callback_query(F.data.startswith("group_extend:"), IsOperator())
async def on_extend(callback: CallbackQuery, session: AsyncSession) -> None:
    chat_id = int(callback.data.split(":", 1)[1])
    repo = GroupRepo(session)
    group = await repo.get_by_chat_id(chat_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    await repo.extend_subscription(group, 30)
    await repo.set_enabled(group, True)
    await session.commit()

    text = await _detail_text(callback.bot, group)
    await callback.message.edit_text(text, reply_markup=group_detail_keyboard(group))
    await callback.answer("30 kunga qo'lda uzaytirildi ✅")


@router.callback_query(F.data.startswith("group_disable:"), IsOperator())
async def on_disable(callback: CallbackQuery, session: AsyncSession) -> None:
    chat_id = int(callback.data.split(":", 1)[1])
    repo = GroupRepo(session)
    group = await repo.get_by_chat_id(chat_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    await repo.set_enabled(group, False)
    await session.commit()

    text = await _detail_text(callback.bot, group)
    await callback.message.edit_text(text, reply_markup=group_detail_keyboard(group))
    await callback.answer("Himoya o'chirildi")
