from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.season import Season
from bot.models.user import User
from bot.repositories.referral_repo import ReferralRepo
from bot.repositories.season_repo import SeasonRepo
from bot.repositories.user_repo import UserRepo

CELEBRATION_EMOJI = "🎉"
_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


@dataclass
class SeasonEndResult:
    closed_season: Season
    new_season: Season
    winner: Optional[User]
    winner_count: int


class SeasonService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.season_repo = SeasonRepo(session)
        self.referral_repo = ReferralRepo(session)
        self.user_repo = UserRepo(session)

    async def get_leaderboard_rows(
        self, season: Season, limit: Optional[int] = 10, offset: int = 0
    ) -> list[dict]:
        rows = await self.referral_repo.season_leaderboard(season.id, limit=limit, offset=offset)
        result = []
        for rank, (referrer_id, count) in enumerate(rows, start=offset + 1):
            user = await self.user_repo.get_by_id(referrer_id)
            result.append(
                {
                    "rank": rank,
                    "user_id": referrer_id,
                    "tg_id": user.tg_id if user else None,
                    "name": user.first_name if user else "Foydalanuvchi",
                    "count": count,
                }
            )
        return result

    async def get_leaderboard_text(
        self, season: Season, limit: int = 10, highlight_user_id: Optional[int] = None
    ) -> str:
        rows = await self.get_leaderboard_rows(season, limit=limit)
        if not rows or rows[0]["count"] == 0:
            return f"🏆 {season.name} reytingi\n\nHali hech kim tasdiqlangan taklif qilmagan."

        lines = [f"🏆 {season.name} reytingi (TOP {len(rows)}):", ""]
        in_top = False
        for row in rows:
            marker = _MEDALS.get(row["rank"], f"{row['rank']}.")
            is_you = highlight_user_id == row["user_id"]
            in_top = in_top or is_you
            lines.append(f"{marker} {row['name']} — {row['count']} ta" + (" 👈 siz" if is_you else ""))

        if highlight_user_id is not None and not in_top:
            position = await self.referral_repo.season_rank_of(season.id, highlight_user_id)
            if position:
                rank, count = position
                lines.append("")
                lines.append(f"Sizning o'rningiz: {rank}-o'rin — {count} ta")

        return "\n".join(lines)

    async def end_current_and_start_new(self, new_season_name: str) -> SeasonEndResult:
        active = await self.season_repo.get_active()
        top = await self.referral_repo.season_leaderboard(active.id, limit=1)

        winner: Optional[User] = None
        winner_count = 0
        if top and top[0][1] > 0:
            winner_id, winner_count = top[0]
            winner = await self.user_repo.get_by_id(winner_id)

        new_season = await self.season_repo.close_and_start_next(
            active, winner.id if winner else None, winner_count if winner else None, new_season_name
        )
        return SeasonEndResult(
            closed_season=active, new_season=new_season, winner=winner, winner_count=winner_count
        )
