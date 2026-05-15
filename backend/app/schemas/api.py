from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


PitchType = Literal["green", "flat", "dusty", "slow", "worn"]
BoundarySize = Literal["large", "medium", "small"]
ModeType = Literal["ai_vs_ai", "user_vs_ai", "user_vs_user", "quicksim"]
BattingMindset = Literal["ultra_defensive", "defensive", "balanced", "aggressive", "ultra_aggressive"]


# ─── Existing schemas ─────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    team1: str
    team2: str
    venue: str
    pitch_type: PitchType = "flat"
    weather_humidity: float = Field(default=0.4, ge=0, le=1)
    dew: bool = False
    toss_winner: Optional[str] = None
    toss_decision: Optional[Literal["bat", "bowl"]] = None
    mode: ModeType = "ai_vs_ai"


class TournamentRequest(BaseModel):
    teams: List[str]
    venue: str
    pitch_type: PitchType = "flat"
    weather_humidity: float = Field(default=0.4, ge=0, le=1)
    dew: bool = False


class PredictRequest(BaseModel):
    team1: str
    team2: str
    venue: str
    pitch_type: PitchType = "flat"
    weather_humidity: float = Field(default=0.4, ge=0, le=1)
    dew: bool = False
    runs: int = Field(default=1000, ge=10, le=5000)


class PlayerOverride(BaseModel):
    team: str
    out_player: str
    in_player: str


class AlternateHistoryRequest(BaseModel):
    team1: str
    team2: str
    venue: str
    pitch_type: PitchType = "flat"
    weather_humidity: float = Field(default=0.4, ge=0, le=1)
    dew: bool = False
    overrides: List[PlayerOverride] = []


class CommentaryRequest(BaseModel):
    tone: Literal["normal", "hype", "meme"] = "normal"
    match_state: Dict[str, str | int | float | bool]


# ─── Game session schemas ─────────────────────────────────────────────────────

class NewGameRequest(BaseModel):
    mode: ModeType
    team1: str
    team2: str
    venue: str
    pitch_type: PitchType = "flat"
    weather_humidity: float = Field(default=0.4, ge=0, le=1)
    dew: bool = False


class SetLineupPayload(BaseModel):
    team: Literal["team1", "team2"] = "team1"
    player_ids: List[int]
    captain_id: int
    wk_id: int


class TossDecisionPayload(BaseModel):
    toss_winner: str
    decision: Literal["bat", "bowl"]


class SetMindsetPayload(BaseModel):
    player_id: int
    mindset: BattingMindset


class BowlPayload(BaseModel):
    field_placement: List[str] = []
    line: Optional[Literal["off_stump", "middle", "leg_stump", "wide"]] = None
    length: Optional[Literal["full", "good_length", "short", "bouncer"]] = None
    aggression: Optional[Literal["defensive", "normal", "attacking"]] = None


class SelectBatterPayload(BaseModel):
    player_id: int


class GameActionRequest(BaseModel):
    action_type: Literal[
        "set_lineup",
        "toss_decision",
        "set_mindset",
        "sim_ball",
        "sim_over",
        "bowl",
        "select_batter",
        "start_innings2",
    ]
    payload: Dict[str, Any] = {}
