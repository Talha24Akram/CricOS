from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import Player, PlayerMatchStats, PlayerRating


def compute_overall(rating: PlayerRating, role: str) -> int:
    """Weighted average of ratings by player role."""
    bat_avg = (
        rating.power + rating.timing + rating.pace_handling + rating.spin_handling
        + rating.strike_rotation + rating.aggression + rating.temperament
        + rating.clutch + rating.death_performance
    ) / 9

    bowl_avg = (
        rating.pace + rating.swing + rating.seam + rating.spin + rating.yorkers
        + rating.variations + rating.control + rating.death_bowling + rating.pressure_handling
    ) / 9

    field_avg = (
        rating.catching + rating.ground_fielding + rating.throwing + rating.fielding_range
    ) / 4

    wk_avg = (
        rating.glove_work + rating.stumping + rating.diving_reflexes + rating.wk_footwork
    ) / 4

    lead_avg = (rating.captaincy + rating.match_reading + rating.man_management) / 3

    if role == "batter":
        overall = bat_avg * 0.70 + bowl_avg * 0.10 + field_avg * 0.15 + lead_avg * 0.05
    elif role == "bowler":
        overall = bat_avg * 0.10 + bowl_avg * 0.70 + field_avg * 0.15 + lead_avg * 0.05
    elif role == "all_rounder":
        overall = bat_avg * 0.40 + bowl_avg * 0.40 + field_avg * 0.15 + lead_avg * 0.05
    elif role == "wicket_keeper":
        overall = bat_avg * 0.50 + wk_avg * 0.30 + field_avg * 0.15 + lead_avg * 0.05
    else:
        overall = bat_avg * 0.40 + bowl_avg * 0.40 + field_avg * 0.15 + lead_avg * 0.05

    return max(1, min(99, round(overall)))


def update_ratings_after_match(db: Session, match_stats: List[PlayerMatchStats]) -> None:
    """Nudge ratings based on match performance."""
    for stat in match_stats:
        player = db.execute(select(Player).where(Player.id == stat.player_id)).scalar_one_or_none()
        rating = db.execute(
            select(PlayerRating).where(
                PlayerRating.player_id == stat.player_id,
                PlayerRating.version == "latest",
            )
        ).scalar_one_or_none()

        if player is None or rating is None:
            continue

        delta_bat = 0.0
        delta_bowl = 0.0

        balls_faced = max(1, stat.balls_faced)
        sr = (stat.runs / balls_faced) * 100 if stat.balls_faced > 0 else 0

        if stat.runs >= 50:
            delta_bat += 0.8
        elif stat.runs >= 30:
            delta_bat += 0.4
        elif stat.runs < 10 and stat.out and stat.balls_faced >= 6:
            delta_bat -= 0.3

        if sr > 180:
            delta_bat += 0.5
        elif sr < 80 and stat.balls_faced >= 12:
            delta_bat -= 0.2

        if stat.wickets >= 3:
            delta_bowl += 0.8
        elif stat.wickets >= 2:
            delta_bowl += 0.4
        elif stat.wickets == 0 and stat.balls_bowled >= 24:
            delta_bowl -= 0.2

        balls_b = max(1, stat.balls_bowled)
        econ = (stat.runs_conceded / (balls_b / 6)) if stat.balls_bowled > 0 else 0
        if econ < 6.0 and stat.balls_bowled >= 18:
            delta_bowl += 0.3
        elif econ > 12.0 and stat.balls_bowled >= 12:
            delta_bowl -= 0.3

        def nudge(attr: str, delta: float) -> None:
            val = getattr(rating, attr, 50)
            setattr(rating, attr, max(1, min(99, round(val + delta))))

        role = player.role or "all_rounder"
        if role in ("batter", "all_rounder", "wicket_keeper"):
            for attr in ("timing", "power", "clutch", "death_performance"):
                nudge(attr, delta_bat)
        if role in ("bowler", "all_rounder"):
            for attr in ("control", "variations", "death_bowling"):
                nudge(attr, delta_bowl)

        rating.overall = compute_overall(rating, role)
        db.flush()

    db.commit()
