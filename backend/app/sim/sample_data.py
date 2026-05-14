from __future__ import annotations

from typing import List

from .entities import BatterRatings, BowlerRatings, Player, Team


def _batter(
    power: int,
    timing: int,
    pace_handling: int,
    spin_handling: int,
    strike_rotation: int,
    aggression: int,
    temperament: int,
    clutch: int,
    death_performance: int,
) -> BatterRatings:
    return BatterRatings(
        power=power,
        timing=timing,
        pace_handling=pace_handling,
        spin_handling=spin_handling,
        strike_rotation=strike_rotation,
        aggression=aggression,
        temperament=temperament,
        clutch=clutch,
        death_performance=death_performance,
    )


def _bowler(
    pace: int,
    swing: int,
    seam: int,
    spin: int,
    yorkers: int,
    variations: int,
    control: int,
    death_bowling: int,
    pressure_handling: int,
) -> BowlerRatings:
    return BowlerRatings(
        pace=pace,
        swing=swing,
        seam=seam,
        spin=spin,
        yorkers=yorkers,
        variations=variations,
        control=control,
        death_bowling=death_bowling,
        pressure_handling=pressure_handling,
    )


def build_sample_teams() -> List[Team]:
    team_a = Team(
        id="IND",
        name="India",
        players=[
            Player(
                id="ind-1",
                name="Rohit",
                role="batter",
                batting=_batter(86, 88, 80, 84, 82, 87, 79, 85, 88),
                bowling=_bowler(25, 20, 20, 18, 10, 18, 15, 10, 25),
                bowling_style="pace",
                arm="right",
            ),
            Player(
                id="ind-2",
                name="Kohli",
                role="batter",
                batting=_batter(78, 94, 90, 89, 95, 74, 94, 93, 83),
                bowling=_bowler(20, 15, 12, 10, 8, 12, 15, 10, 20),
                bowling_style="pace",
                arm="right",
            ),
            Player(
                id="ind-3",
                name="Surya",
                role="batter",
                batting=_batter(92, 90, 88, 85, 84, 93, 80, 86, 94),
                bowling=_bowler(20, 12, 10, 14, 8, 15, 12, 10, 18),
                bowling_style="spin",
                arm="right",
            ),
            Player(
                id="ind-4",
                name="Hardik",
                role="all_rounder",
                batting=_batter(84, 80, 76, 74, 72, 88, 74, 82, 90),
                bowling=_bowler(82, 72, 74, 30, 78, 74, 76, 80, 78),
                bowling_style="pace",
                arm="right",
            ),
            Player(
                id="ind-5",
                name="Jadeja",
                role="all_rounder",
                batting=_batter(68, 75, 70, 82, 86, 65, 84, 80, 72),
                bowling=_bowler(42, 35, 38, 84, 56, 72, 82, 70, 83),
                bowling_style="spin",
                arm="left",
            ),
            Player(
                id="ind-6",
                name="Bumrah",
                role="bowler",
                batting=_batter(40, 42, 38, 36, 28, 35, 65, 70, 55),
                bowling=_bowler(93, 86, 88, 20, 95, 90, 92, 95, 94),
                bowling_style="pace",
                arm="right",
            ),
        ],
    )

    team_b = Team(
        id="AUS",
        name="Australia",
        players=[
            Player(
                id="aus-1",
                name="Warner",
                role="batter",
                batting=_batter(84, 86, 83, 82, 80, 89, 76, 82, 86),
                bowling=_bowler(15, 12, 10, 8, 6, 8, 10, 6, 12),
                bowling_style="pace",
                arm="left",
            ),
            Player(
                id="aus-2",
                name="Head",
                role="batter",
                batting=_batter(88, 84, 80, 79, 78, 90, 74, 79, 90),
                bowling=_bowler(18, 14, 12, 10, 8, 10, 12, 8, 14),
                bowling_style="pace",
                arm="left",
            ),
            Player(
                id="aus-3",
                name="Maxwell",
                role="all_rounder",
                batting=_batter(90, 82, 78, 84, 76, 94, 70, 80, 92),
                bowling=_bowler(30, 24, 22, 76, 45, 68, 70, 65, 72),
                bowling_style="spin",
                arm="right",
            ),
            Player(
                id="aus-4",
                name="Stoinis",
                role="all_rounder",
                batting=_batter(82, 76, 74, 70, 72, 86, 72, 76, 88),
                bowling=_bowler(76, 66, 70, 26, 72, 68, 72, 74, 74),
                bowling_style="pace",
                arm="right",
            ),
            Player(
                id="aus-5",
                name="Zampa",
                role="bowler",
                batting=_batter(38, 40, 35, 40, 28, 30, 62, 64, 48),
                bowling=_bowler(28, 20, 22, 88, 58, 82, 78, 72, 80),
                bowling_style="spin",
                arm="right",
            ),
            Player(
                id="aus-6",
                name="Starc",
                role="bowler",
                batting=_batter(45, 44, 42, 38, 30, 42, 68, 72, 60),
                bowling=_bowler(90, 90, 84, 24, 92, 85, 86, 90, 88),
                bowling_style="pace",
                arm="left",
            ),
        ],
    )

    return [team_a, team_b]
