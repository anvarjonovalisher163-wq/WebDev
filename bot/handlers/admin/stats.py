import tempfile
from pathlib import Path

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import CB_ADMIN_STATS, CB_ADMIN_STATS_CSV, stats_menu_keyboard
from bot.repositories.settings_repo import SettingsRepo
from bot.services.export import stats_to_csv
from bot.services.stats_service import StatsService

router = Router(name="admin_stats")


def _format_report(general: dict, referral: dict, funnel: dict, top: list) -> str:
    top_lines = "\n".join(
        f"{i + 1}. {user.first_name} (@{user.username or '-'}) - {cnt} ta"
        for i, (user, cnt) in enumerate(top)
    ) or "(hali yo'q)"

    return (
        "<b>Umumiy statistika</b>\n"
        f"Jami /start bosganlar: {general['total_users']}\n"
        f"Bugun qo'shilganlar: {general['today_users']}\n"
        f"Oxirgi 7 kunda: {general['last_7d_users']}\n"
        f"Oxirgi 30 kunda: {general['last_30d_users']}\n"
        f"Barcha kanallarga obuna bo'lganlar: {general['subscribed']}\n"
        f"Referral havola yaratganlar: {general['generated_link']}\n"
        f"Kamida bitta taklif qilganlar: {general['at_least_one_referral']}\n"
        f"Barcha shartlarni bajarganlar: {general['completed_all_requirements']}\n"
        f"Maxfiy havola olganlar: {general['secret_link_taken']}\n"
        f"Yopiq kanalga qo'shilganlar: {general['joined_private']}\n"
        f"Botni bloklaganlar: {general['blocked']}\n\n"
        "<b>Referral statistikasi</b>\n"
        f"Jami referral: {referral['total']}\n"
        f"Tasdiqlangan: {referral['approved']}\n"
        f"Shartlarni bajarmagan: {referral['pending']}\n"
        f"Konversiya: {referral['conversion_pct']}%\n\n"
        "<b>Konversiya voronkasi</b>\n"
        f"/start → obuna: {funnel['start_to_subscribed']}%\n"
        f"obuna → havola olish: {funnel['subscribed_to_link']}%\n"
        f"havola → shartlarni bajarish: {funnel['link_to_completed']}%\n"
        f"shartlar → maxfiy havola: {funnel['completed_to_secret']}%\n"
        f"maxfiy havola → kanalga qo'shilish: {funnel['secret_to_joined']}%\n\n"
        f"<b>Top {len(top)} taklif qiluvchi</b>\n{top_lines}"
    )


async def _collect(session: AsyncSession):
    settings = await SettingsRepo(session).get()
    stats_service = StatsService(session)
    general = await stats_service.general_stats(settings.required_referral_count)
    referral = await stats_service.referral_stats()
    funnel = stats_service.conversion_funnel(general)
    top = await stats_service.top_referrers(10)
    return general, referral, funnel, top


@router.callback_query(lambda c: c.data == CB_ADMIN_STATS)
async def on_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    general, referral, funnel, top = await _collect(session)
    await callback.message.edit_text(
        _format_report(general, referral, funnel, top), reply_markup=stats_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == CB_ADMIN_STATS_CSV)
async def on_stats_csv(callback: CallbackQuery, session: AsyncSession) -> None:
    general, referral, funnel, top = await _collect(session)
    csv_content = stats_to_csv(general, referral, funnel, top)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8-sig", newline=""
    ) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        await callback.message.answer_document(
            FSInputFile(tmp_path, filename="statistika.csv"), caption="Statistika CSV eksporti"
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    await callback.answer()
