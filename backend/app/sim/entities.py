from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

Phase = Literal["powerplay", "middle", "death"]
BowlingStyle = Literal["pace", "spin"]
Arm = Literal["left", "right"]


@dataclass(frozen=True)
class BatterRatings:
    power: int
    timing: int
    pace_handling: int
    spin_handling: int
    strike_rotation: int
    aggression: int
    temperament: int
    clutch: int
    death_performance: int


@dataclass(frozen=True)
class BowlerRatings:
    pace: int
    swing: int
    seam: int
    spin: int
    yorkers: int
    variations: int
    control: int
    death_bowling: int
    pressure_handling: int


@dataclass(frozen=True)
class Player:
    id: str
    name: str
    role: Literal["batter", "bowler", "all_rounder", "wk"]
    batting: BatterRatings
    bowling: BowlerRatings
    bowling_style: BowlingStyle
    arm: Arm


@dataclass(frozen=True)
class Team:
    id: str
    name: str
    players: List[Player]


@dataclass
class BattingLine:
    player_id: str
    player_name: str
    runs: int = 0
    balls: int = 0
    fours: int = 0
    sixes: int = 0
    out: bool = False


@dataclass
class BowlingLine:
    player_id: str
    player_name: str
    balls: int = 0
    runs: int = 0
    wickets: int = 0


@dataclass
class BallEvent:
    over: int
    ball_in_over: int
    phase: Phase
    striker: str
    bowler: str
    outcome: str
    runs: int
    wicket: bool
    score_after: int
    wickets_after: int


@dataclass
class InningsResult:
    batting_team: str
    bowling_team: str
    runs: int
    wickets: int
    balls_faced: int
    events: List[BallEvent]
    batting_card: Dict[str, BattingLine]
    bowling_card: Dict[str, BowlingLine]
    over_summary: List[str] = field(default_factory=list)


@dataclass
class MatchResult:
    first_innings: InningsResult
    second_innings: InningsResult
    winner: str
    margin: str
