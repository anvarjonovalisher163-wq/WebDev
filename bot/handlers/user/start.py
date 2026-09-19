from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings as app_settings
from bot.handlers.user._common import check_gate, finalize_subscription, get_gate_text, get_welcome_text
from bot.keyboards.admin import admin_settings_reply_keyboard
from bot.keyboards.user import DEFAULT_SHARE_TEXT, subscription_gate_keyboard, welcome_actions_keyboard
from bot.repositories.admin_repo import AdminRepo
from bot.repositories.settings_repo import SettingsRepo
from bot.services.referral_service import ReferralService
from bot.services.subscription_service import SubscriptionService
from bot.services.user_service import UserService, build_referral_link

router = Router(name="user_start")


@router.message(CommandStart())
async def cmd_start(
    message: Message, command: CommandObject, session: AsyncSession, bot: Bot, bot_username: str
) -> None:
    tg_user = message.from_user

    # Pastki (reply) klaviaturani sozlaymiz. Admin uchun doimiy "Sozlamalar"
    # tugmasini o'rnatuvchi xabar o'chirilmaydi - Telegram mijozlari
    # klaviaturani o'rnatgan xabar o'chirilganda uni yashirib qo'yishi mumkin,
    # shuning uchun bu xabar ekranda qoladi. Oddiy foydalanuvchilar uchun esa
    # eski klaviaturani tozalovchi xabar ko'rinmas tarzda o'chiriladi (maqsad
    # "klaviatura yo'q" holati, uni o'chirish bu holatni buzmaydi).
    is_admin = await AdminRepo(session).get_by_tg_id(tg_user.id) is not None
    if is_admin:
        await message.answer("⚙️ Admin rejimi yoqilgan.", reply_markup=admin_settings_reply_keyboard())
    else:
        cleanup = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
        await cleanup.delete()

    subscription_service = SubscriptionService(bot)
    referral_service = ReferralService(session, subscription_service)
    user_service = UserService(session, referral_service)

    result = await user_service.register_or_touch(
        tg_id=tg_user.id,
        first_name=tg_user.first_name or "",
        last_name=tg_user.last_name,
        username=tg_user.username,
        start_payload=command.args,
    )
    await session.commit()

    user = result.user
    if user.is_blocked:
        await message.answer("Siz botdan foydalanish huquqidan mahrum qilingansiz.")
        return

    is_subscribed, not_subscribed = await check_gate(session, subscription_service, user)
    if not is_subscribed:
        user.is_subscribed = False
        await session.commit()
        settings = await SettingsRepo(session).get()
        await message.answer(
            get_gate_text(settings),
            reply_markup=subscription_gate_keyboard(not_subscribed),
        )
        return

    await finalize_subscription(session, bot, user, referral_service)
    await session.commit()

    settings = await SettingsRepo(session).get()
    link = build_referral_link(bot_username, user.tg_id)
    welcome_text = get_welcome_text(settings, user.first_name, link)
    keyboard = welcome_actions_keyboard(
        link, settings.share_text or DEFAULT_SHARE_TEXT, app_settings.webapp_url
    )

    if settings.welcome_media_file_id and settings.welcome_media_type == "photo":
        await message.answer_photo(settings.welcome_media_file_id, caption=welcome_text, reply_markup=keyboard)
    elif settings.welcome_media_file_id and settings.welcome_media_type == "video":
        await message.answer_video(settings.welcome_media_file_id, caption=welcome_text, reply_markup=keyboard)
    else:
        await message.answer(welcome_text, reply_markup=keyboard)
