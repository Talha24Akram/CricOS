from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.models.tables import Player, PlayerRating, Team, TeamPlayer, Venue
from app.schemas.api import AlternateHistoryRequest, CommentaryRequest, PredictRequest, SimulateRequest, TournamentRequest
from app.services.commentary import generate_commentary_line
from app.services.simulation_service import predict_match, simulate_alternate_history, simulate_once, simulate_tournament

router = APIRouter()


@router.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    teams = db.execute(select(Team)).scalars().all()
    out = []
    for team in teams:
        links = db.execute(select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.is_active.is_(True))).scalars().all()
        players = db.execute(select(Player).where(Player.id.in_([l.player_id for l in links]))).scalars().all() if links else []
        out.append({"id": team.id, "name": team.name, "short_code": team.short_code, "squad": [p.name for p in players]})
    return out


@router.get("/players/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.execute(select(Player).where(Player.id == player_id)).scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    rating = db.execute(select(PlayerRating).where(PlayerRating.player_id == player_id, PlayerRating.version == "latest")).scalar_one_or_none()
    return {
        "id": player.id,
        "name": player.name,
        "batting_style": player.batting_style,
        "bowling_style": player.bowling_style,
        "arm": player.arm,
        "ratings": rating.raw_snapshot if rating else None,
    }


@router.get("/venues")
def get_venues(db: Session = Depends(get_db)):
    venues = db.execute(select(Venue)).scalars().all()
    return [
        {
            "id": v.id,
            "name": v.name,
            "city": v.city,
            "boundary_size": v.boundary_size,
            "six_multiplier": v.six_multiplier,
            "pace_multiplier": v.pace_multiplier,
            "spin_multiplier": v.spin_multiplier,
        }
        for v in venues
    ]


@router.post("/simulate")
def simulate(request: SimulateRequest, db: Session = Depends(get_db)):
    try:
        return simulate_once(
            db,
            team1_name=request.team1,
            team2_name=request.team2,
            venue_name=request.venue,
            pitch_type=request.pitch_type,
            humidity=request.weather_humidity,
            dew=request.dew,
            seed=42,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/predict")
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    try:
        return predict_match(
            db,
            team1_name=request.team1,
            team2_name=request.team2,
            venue_name=request.venue,
            pitch_type=request.pitch_type,
            humidity=request.weather_humidity,
            dew=request.dew,
            runs=request.runs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tournament")
def tournament(request: TournamentRequest, db: Session = Depends(get_db)):
    try:
        return simulate_tournament(
            db,
            teams=request.teams,
            venue=request.venue,
            pitch_type=request.pitch_type,
            humidity=request.weather_humidity,
            dew=request.dew,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/alternate-history")
def alternate_history(request: AlternateHistoryRequest, db: Session = Depends(get_db)):
    try:
        return simulate_alternate_history(
            db,
            team1_name=request.team1,
            team2_name=request.team2,
            venue_name=request.venue,
            pitch_type=request.pitch_type,
            humidity=request.weather_humidity,
            dew=request.dew,
            overrides=[o.model_dump() for o in request.overrides],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/commentary")
def commentary(request: CommentaryRequest):
    return {"commentary": generate_commentary_line(request.match_state, request.tone)}
