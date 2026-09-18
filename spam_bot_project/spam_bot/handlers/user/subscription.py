from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from spam_bot.config import settings
from spam_bot.filters.is_group_admin import IsGroupAdmin
from spam_bot.repositories.group_repo import GroupRepo
from spam_bot.repositories.payment_log_repo import PaymentLogRepo
from spam_bot.services.notify import notify_operators
from spam_bot.utils.copy import (
    SUBSCRIPTION_GROUP_ONLY,
    SUBSCRIPTION_INVOICE_DESCRIPTION,
    SUBSCRIPTION_INVOICE_TITLE,
    SUBSCRIPTION_LABEL,
    SUBSCRIPTION_PAID_DM,
    SUBSCRIPTION_PAID_GROUP,
)

router = Router(name="subscription")

_PAYLOAD_PREFIX = "sub"


@router.message(Command("obuna"), F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())
async def cmd_obuna(message: Message, bot: Bot) -> None:
    payload = f"{_PAYLOAD_PREFIX}:{message.chat.id}:{message.from_user.id}"
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=SUBSCRIPTION_INVOICE_TITLE,
        description=SUBSCRIPTION_INVOICE_DESCRIPTION.format(
            group=message.chat.title or str(message.chat.id), days=settings.subscription_period_days
        ),
        payload=payload,
        provider_token="",  # Telegram Stars uchun bo'sh qoldiriladi
        currency="XTR",
        prices=[LabeledPrice(label=SUBSCRIPTION_LABEL.format(days=settings.subscription_period_days), amount=settings.subscription_price_stars)],
    )


@router.message(Command("obuna"), F.chat.type == "private")
async def cmd_obuna_private(message: Message) -> None:
    await message.answer(SUBSCRIPTION_GROUP_ONLY)


@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot) -> None:
    payload = pre_checkout_query.invoice_payload
    if not payload.startswith(f"{_PAYLOAD_PREFIX}:"):
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Noto'g'ri buyurtma.")
        return
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, bot: Bot, session: AsyncSession) -> None:
    payment = message.successful_payment
    parts = payment.invoice_payload.split(":")
    if len(parts) != 3 or parts[0] != _PAYLOAD_PREFIX:
        logger.warning(f"Noma'lum to'lov payload'i: {payment.invoice_payload}")
        return
    chat_id, admin_id = int(parts[1]), int(parts[2])

    group_repo = GroupRepo(session)
    group = await group_repo.get_by_chat_id(chat_id)
    if group is None:
        logger.warning(f"To'lov qilingan guruh topilmadi: {chat_id}")
        return

    new_until = await group_repo.extend_subscription(group, settings.subscription_period_days)
    if not group.enabled:
        await group_repo.set_enabled(group, True)
    await PaymentLogRepo(session).add(chat_id, message.from_user.id, payment.total_amount)
    await session.commit()

    until_str = new_until.strftime("%Y-%m-%d")
    await message.answer(SUBSCRIPTION_PAID_GROUP.format(until=until_str))

    if message.from_user.id != admin_id:
        try:
            await bot.send_message(admin_id, SUBSCRIPTION_PAID_DM.format(group=group.title or str(chat_id), until=until_str))
        except TelegramForbiddenError:
            pass

    await notify_operators(
        bot,
        f"💰 <b>{group.title or chat_id}</b> guruhidan {payment.total_amount} Stars to'lov qabul qilindi (obuna {until_str} gacha).",
    )
