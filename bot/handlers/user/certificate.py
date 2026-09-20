from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepo
from bot.states.user_states import CertificateStates

router = Router(name="user_certificate")


@router.message(CertificateStates.waiting_full_name, F.text)
async def on_full_name_received(
    message: Message, session: AsyncSession, state: FSMContext
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

    user.cert_full_name = full_name
    user.cert_requested_at = datetime.now(timezone.utc)
    await session.commit()

    await state.clear()
    await message.answer(
        f"Rahmat, {full_name}! Ma'lumotlaringiz qabul qilindi.\n\n"
        "Sertifikatingiz loyiha/mavsum yakunida ushbu bot orqali yuboriladi."
    )


@router.message(CertificateStates.waiting_full_name)
async def on_full_name_invalid(message: Message) -> None:
    await message.answer(
        "Iltimos, to'liq ism va familiyangizni matn ko'rinishida yuboring "
        "(masalan: Anvar Anvarov):"
    )
