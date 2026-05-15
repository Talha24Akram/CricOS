from __future__ import annotations

from typing import Dict, List

from sqlalchemy import Integer, select, func
from sqlalchemy.orm import Session

from app.models.tables import (
    GameSession, MatchRecord, Player, PlayerMatchStats,
    PlayerRating, Team, TeamPlayer,
)
from app.sim.entities import InningsResult, MatchResult


def record_match(db: Session, session: GameSession, match: MatchResult) -> MatchRecord:
    """Persist a completed match and per-player stats."""
    record = MatchRecord(
        session_id=session.id,
        team1=session.team1_name,
        team2=session.team2_name,
        winner=match.winner,
        margin=match.margin,
        venue=session.venue_name,
        mode=session.mode,
    )
    db.add(record)
    db.flush()

    _write_innings_stats(db, record, match.first_innings, session)
    _write_innings_stats(db, record, match.second_innings, session)

    db.commit()
    db.refresh(record)
    return record


def _write_innings_stats(
    db: Session, record: MatchRecord, innings: InningsResult, session: GameSession
) -> None:
    team_name = innings.batting_team

    # Resolve DB player IDs from sim player IDs (stored as str(db_id))
    for sim_pid, bat_line in innings.batting_card.items():
        try:
            db_pid = int(sim_pid)
        except ValueError:
            continue

        stat = db.execute(
            select(PlayerMatchStats).where(
                PlayerMatchStats.match_id == record.id,
                PlayerMatchStats.player_id == db_pid,
            )
        ).scalar_one_or_none()

        if stat is None:
            stat = PlayerMatchStats(match_id=record.id, player_id=db_pid, team=team_name)
            db.add(stat)

        stat.runs = bat_line.runs
        stat.balls_faced = bat_line.balls
        stat.fours = bat_line.fours
        stat.sixes = bat_line.sixes
        stat.out = bat_line.out

    for sim_pid, bowl_line in innings.bowling_card.items():
        try:
            db_pid = int(sim_pid)
        except ValueError:
            continue

        stat = db.execute(
            select(PlayerMatchStats).where(
                PlayerMatchStats.match_id == record.id,
                PlayerMatchStats.player_id == db_pid,
            )
        ).scalar_one_or_none()

        if stat is None:
            stat = PlayerMatchStats(
                match_id=record.id,
                player_id=db_pid,
                team=innings.bowling_team,
            )
            db.add(stat)

        stat.wickets = bowl_line.wickets
        stat.balls_bowled = bowl_line.balls
        stat.runs_conceded = bowl_line.runs

    db.flush()


def get_player_career_stats(db: Session, player_id: int) -> Dict:
    player = db.execute(select(Player).where(Player.id == player_id)).scalar_one_or_none()
    if player is None:
        return {}

    rating = db.execute(
        select(PlayerRating).where(
            PlayerRating.player_id == player_id,
            PlayerRating.version == "latest",
        )
    ).scalar_one_or_none()

    sim_stats = db.execute(
        select(
            func.count(PlayerMatchStats.id).label("matches"),
            func.sum(PlayerMatchStats.runs).label("runs"),
            func.sum(PlayerMatchStats.balls_faced).label("balls_faced"),
            func.sum(PlayerMatchStats.fours).label("fours"),
            func.sum(PlayerMatchStats.sixes).label("sixes"),
            func.sum(PlayerMatchStats.out.cast(Integer)).label("outs"),
            func.sum(PlayerMatchStats.wickets).label("wickets"),
            func.sum(PlayerMatchStats.balls_bowled).label("balls_bowled"),
            func.sum(PlayerMatchStats.runs_conceded).label("runs_conceded"),
        ).where(PlayerMatchStats.player_id == player_id)
    ).one_or_none()

    matches = int(sim_stats.matches or 0)
    runs = int(sim_stats.runs or 0)
    bf = int(sim_stats.balls_faced or 0)
    fours = int(sim_stats.fours or 0)
    sixes = int(sim_stats.sixes or 0)
    outs = int(sim_stats.outs or 0)
    wickets = int(sim_stats.wickets or 0)
    balls_b = int(sim_stats.balls_bowled or 0)
    runs_c = int(sim_stats.runs_conceded or 0)

    bat_avg = round(runs / outs, 1) if outs > 0 else runs
    bat_sr = round((runs / bf) * 100, 1) if bf > 0 else 0.0
    bowl_avg = round(runs_c / wickets, 1) if wickets > 0 else 0.0
    bowl_econ = round((runs_c / (balls_b / 6)), 2) if balls_b > 0 else 0.0
    bowl_sr = round(balls_b / wickets, 1) if wickets > 0 else 0.0

    return {
        "player_id": player_id,
        "name": player.name,
        "role": player.role,
        "photo_url": player.photo_url,
        "overall": rating.overall if rating else 50,
        "sim_batting": {
            "matches": matches,
            "runs": runs,
            "balls_faced": bf,
            "average": bat_avg,
            "strike_rate": bat_sr,
            "fours": fours,
            "sixes": sixes,
            "dismissals": outs,
        },
        "sim_bowling": {
            "wickets": wickets,
            "balls_bowled": balls_b,
            "runs_conceded": runs_c,
            "average": bowl_avg,
            "economy": bowl_econ,
            "strike_rate": bowl_sr,
        },
    }


def get_team_stats(db: Session, team_name: str) -> List[Dict]:
    team = db.execute(select(Team).where(Team.name == team_name)).scalar_one_or_none()
    if team is None:
        return []

    links = db.execute(
        select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.is_active.is_(True))
    ).scalars().all()

    return [get_player_career_stats(db, link.player_id) for link in links]
