from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user._common import check_gate, finalize_subscription, get_gate_text, get_welcome_text
from bot.keyboards.user import DEFAULT_SHARE_TEXT, subscription_gate_keyboard, welcome_actions_keyboard
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

    # Eski pastki (reply) klaviatura hali foydalanuvchi ekranida qolgan bo'lishi
    # mumkin - uni bosishni kutmasdan avtomatik tozalaymiz.
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
    welcome_text = get_welcome_text(settings)
    link = build_referral_link(bot_username, user.tg_id)
    keyboard = welcome_actions_keyboard(link, settings.share_text or DEFAULT_SHARE_TEXT)

    if settings.welcome_media_file_id and settings.welcome_media_type == "photo":
        await message.answer_photo(settings.welcome_media_file_id, caption=welcome_text, reply_markup=keyboard)
    elif settings.welcome_media_file_id and settings.welcome_media_type == "video":
        await message.answer_video(settings.welcome_media_file_id, caption=welcome_text, reply_markup=keyboard)
    else:
        await message.answer(welcome_text, reply_markup=keyboard)
