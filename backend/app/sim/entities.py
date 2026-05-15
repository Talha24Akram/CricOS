from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

Phase = Literal["powerplay", "middle", "death"]
BowlingStyle = Literal["pace", "spin"]
Arm = Literal["left", "right"]
BattingMindset = Literal["ultra_defensive", "defensive", "balanced", "aggressive", "ultra_aggressive"]


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
class FieldingRatings:
    catching: int = 50
    ground_fielding: int = 50
    throwing: int = 50
    fielding_range: int = 50


@dataclass(frozen=True)
class WKRatings:
    glove_work: int = 50
    stumping: int = 50
    diving_reflexes: int = 50
    wk_footwork: int = 50


@dataclass(frozen=True)
class LeadershipRatings:
    captaincy: int = 50
    match_reading: int = 50
    man_management: int = 50


@dataclass(frozen=True)
class Player:
    id: str
    name: str
    role: Literal["batter", "bowler", "all_rounder", "wicket_keeper"]
    batting: BatterRatings
    bowling: BowlerRatings
    bowling_style: BowlingStyle
    arm: Arm
    fielding: FieldingRatings = field(default_factory=FieldingRatings)
    wk: WKRatings = field(default_factory=WKRatings)
    leadership: LeadershipRatings = field(default_factory=LeadershipRatings)
    overall: int = 60


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
    shot_zone: str = ""
    delivery_type: str = "hard_length"
    mindset: str = "balanced"
    striker_id: str = ""
    bowler_id: str = ""


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
