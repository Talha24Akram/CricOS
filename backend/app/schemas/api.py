from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


PitchType = Literal["green", "flat", "dusty", "slow", "worn"]
BoundarySize = Literal["large", "medium", "small"]
ModeType = Literal["ai_vs_ai", "user_vs_ai", "user_vs_user", "quicksim"]


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
