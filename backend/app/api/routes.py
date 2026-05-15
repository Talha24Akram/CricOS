from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.models.tables import Player, PlayerRating, Team, TeamPlayer, Venue
from app.schemas.api import (
    AlternateHistoryRequest, CommentaryRequest, GameActionRequest,
    NewGameRequest, PredictRequest, SimulateRequest, TournamentRequest,
)
from app.services.commentary import generate_commentary_line
from app.services.game_service import create_session, get_state, post_action
from app.services.simulation_service import (
    predict_match, simulate_alternate_history, simulate_once, simulate_tournament,
)
from app.services.stats_service import get_player_career_stats, get_team_stats

router = APIRouter()


# ─── Lookup endpoints ─────────────────────────────────────────────────────────

@router.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    teams = db.execute(select(Team)).scalars().all()
    out = []
    for team in teams:
        links = db.execute(
            select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.is_active.is_(True))
        ).scalars().all()
        player_ids = [l.player_id for l in links]
        players = (
            db.execute(select(Player).where(Player.id.in_(player_ids))).scalars().all()
            if player_ids
            else []
        )
        out.append({
            "id": team.id,
            "name": team.name,
            "short_code": team.short_code,
            "logo_url": team.logo_url,
            "squad": [
                {
                    "id": p.id, "name": p.name,
                    "role": p.role, "photo_url": p.photo_url,
                    "cricinfo_id": p.cricinfo_id,
                }
                for p in players
            ],
        })
    return out


@router.get("/players/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.execute(select(Player).where(Player.id == player_id)).scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    rating = db.execute(
        select(PlayerRating).where(
            PlayerRating.player_id == player_id,
            PlayerRating.version == "latest",
        )
    ).scalar_one_or_none()

    return {
        "id": player.id,
        "name": player.name,
        "role": player.role,
        "batting_style": player.batting_style,
        "bowling_style": player.bowling_style,
        "arm": player.arm,
        "photo_url": player.photo_url,
        "cricinfo_id": player.cricinfo_id,
        "ratings": rating.raw_snapshot if rating else None,
        "overall": rating.overall if rating else 50,
    }


@router.get("/players/{player_id}/stats")
def player_stats(player_id: int, db: Session = Depends(get_db)):
    stats = get_player_career_stats(db, player_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Player not found")
    return stats


@router.get("/teams/{team_name}/stats")
def team_stats(team_name: str, db: Session = Depends(get_db)):
    return get_team_stats(db, team_name)


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


# ─── Simulation endpoints ─────────────────────────────────────────────────────

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


# ─── Game session endpoints ───────────────────────────────────────────────────

@router.post("/game/new")
def new_game(request: NewGameRequest, db: Session = Depends(get_db)):
    try:
        session = create_session(
            db,
            mode=request.mode,
            team1=request.team1,
            team2=request.team2,
            venue=request.venue,
            pitch_type=request.pitch_type,
            humidity=request.weather_humidity,
            dew=request.dew,
        )
        return get_state(db, session.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/game/{session_id}")
def game_state(session_id: str, db: Session = Depends(get_db)):
    try:
        return get_state(db, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/game/{session_id}/action")
def game_action(session_id: str, request: GameActionRequest, db: Session = Depends(get_db)):
    try:
        return post_action(db, session_id, request.action_type, request.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
