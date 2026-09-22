from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepo
from bot.services.certificate_approval import submit_certificate_name_for_approval
from bot.states.user_states import CertificateStates

router = Router(name="user_certificate")

MAX_NAME_PART_LENGTH = 120


@router.message(CertificateStates.waiting_full_name, F.text)
async def on_full_name_received(
    message: Message, session: AsyncSession, state: FSMContext, bot: Bot
) -> None:
    full_name = message.text.strip()

    if len(full_name.split()) < 2 or len(full_name) > 255:
        await message.answer(
            "Iltimos, to'liq ism va familiyangizni to'g'ri kiriting "
            "(masalan: Anvar Anvarov):"
        )
        return

    user_repo = UserRepo(session)
    user = await user_repo.get_by_tg_id(message.from_user.id)
    if user is None:
        await state.clear()
        return

    await state.clear()
    await submit_certificate_name_for_approval(session, bot, user, full_name)
    await message.answer(
        f"Rahmat, {full_name}! Ma'lumotlaringiz admin tomonidan tekshirilgach, "
        "sertifikatingiz shu bot orqali yuboriladi."
    )


@router.message(CertificateStates.waiting_full_name)
async def on_full_name_invalid(message: Message) -> None:
    await message.answer(
        "Iltimos, to'liq ism va familiyangizni matn ko'rinishida yuboring "
        "(masalan: Anvar Anvarov):"
    )


@router.message(CertificateStates.waiting_first_name, F.text)
async def on_first_name_received(message: Message, state: FSMContext) -> None:
    first_name = message.text.strip()
    if not first_name or len(first_name) > MAX_NAME_PART_LENGTH:
        await message.answer("Iltimos, ismingizni to'g'ri kiriting (masalan: Anvar):")
        return

    await state.update_data(cert_first_name=first_name)
    await state.set_state(CertificateStates.waiting_last_name)
    await message.answer("Endi familiyangizni kiriting:")


@router.message(CertificateStates.waiting_first_name)
async def on_first_name_invalid(message: Message) -> None:
    await message.answer("Iltimos, ismingizni matn ko'rinishida yuboring:")


@router.message(CertificateStates.waiting_last_name, F.text)
async def on_last_name_received(
    message: Message, session: AsyncSession, state: FSMContext, bot: Bot
) -> None:
    last_name = message.text.strip()
    if not last_name or len(last_name) > MAX_NAME_PART_LENGTH:
        await message.answer("Iltimos, familiyangizni to'g'ri kiriting (masalan: Anvarov):")
        return

    data = await state.get_data()
    first_name = data.get("cert_first_name", "").strip()
    full_name = f"{first_name} {last_name}".strip()
    await state.clear()

    user_repo = UserRepo(session)
    user = await user_repo.get_by_tg_id(message.from_user.id)
    if user is None or not first_name:
        return

    await submit_certificate_name_for_approval(session, bot, user, full_name)
    await message.answer(
        f"Rahmat, {full_name}! Ma'lumotlaringiz admin tomonidan tekshirilgach, "
        "sertifikatingiz shu bot orqali yuboriladi."
    )


@router.message(CertificateStates.waiting_last_name)
async def on_last_name_invalid(message: Message) -> None:
    await message.answer("Iltimos, familiyangizni matn ko'rinishida yuboring:")
