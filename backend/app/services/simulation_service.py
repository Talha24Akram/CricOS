from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import Player, PlayerRating, Team, TeamPlayer, Venue
from app.sim.entities import BatterRatings, BowlerRatings, Player as SimPlayer, Team as SimTeam
from app.sim.engine import SimulationConfig, top_performers
from app.sim.monte_carlo import run_monte_carlo, summary_to_dict
from app.sim.tactical import MatchConditions, simulate_match_with_tactics


def _sim_player_from_db(player: Player, rating: PlayerRating | None) -> SimPlayer:
    def get(attr: str, default: int = 55) -> int:
        return int(getattr(rating, attr, default)) if rating else default

    batting = BatterRatings(
        power=get("power"),
        timing=get("timing"),
        pace_handling=get("pace_handling"),
        spin_handling=get("spin_handling"),
        strike_rotation=get("strike_rotation"),
        aggression=get("aggression"),
        temperament=get("temperament"),
        clutch=get("clutch"),
        death_performance=get("death_performance"),
    )
    bowling = BowlerRatings(
        pace=get("pace"),
        swing=get("swing"),
        seam=get("seam"),
        spin=get("spin"),
        yorkers=get("yorkers"),
        variations=get("variations"),
        control=get("control"),
        death_bowling=get("death_bowling"),
        pressure_handling=get("pressure_handling"),
    )

    bowling_style = "spin" if (player.bowling_style or "").lower().find("spin") >= 0 else "pace"
    arm = "left" if (player.arm or "").lower().startswith("left") else "right"

    return SimPlayer(
        id=str(player.id),
        name=player.name,
        role="all_rounder",
        batting=batting,
        bowling=bowling,
        bowling_style=bowling_style,
        arm=arm,
    )


def get_team_by_name(db: Session, team_name: str) -> SimTeam:
    team = db.execute(select(Team).where(Team.name == team_name)).scalar_one_or_none()
    if team is None:
        raise ValueError(f"Team not found: {team_name}")

    links = db.execute(select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.is_active.is_(True))).scalars().all()
    player_ids = [l.player_id for l in links]
    if not player_ids:
        raise ValueError(f"Team has no players: {team_name}")

    players = db.execute(select(Player).where(Player.id.in_(player_ids))).scalars().all()
    ratings = db.execute(select(PlayerRating).where(PlayerRating.player_id.in_(player_ids), PlayerRating.version == "latest")).scalars().all()
    rating_by_player = {r.player_id: r for r in ratings}

    sim_players = [_sim_player_from_db(p, rating_by_player.get(p.id)) for p in players][:11]
    return SimTeam(id=str(team.id), name=team.name, players=sim_players)


def get_venue_by_name(db: Session, venue_name: str) -> Venue:
    venue = db.execute(select(Venue).where(Venue.name == venue_name)).scalar_one_or_none()
    if venue is None:
        raise ValueError(f"Venue not found: {venue_name}")
    return venue


def _simulate_with_teams(
    team1: SimTeam,
    team2: SimTeam,
    venue: Venue,
    pitch_type: str,
    humidity: float,
    dew: bool,
    seed: int | None = 42,
) -> Dict:
    conditions = MatchConditions(
        pitch_type=pitch_type,
        humidity=humidity,
        dew=dew,
        boundary_size=venue.boundary_size,
    )

    match = simulate_match_with_tactics(team1, team2, SimulationConfig(seed=seed), conditions)
    performers = top_performers(match)

    return {
        "winner": match.winner,
        "margin": match.margin,
        "venue": venue.name,
        "conditions": {
            "pitch_type": pitch_type,
            "humidity": humidity,
            "dew": dew,
            "boundary_size": venue.boundary_size,
        },
        "innings": [
            {
                "team": match.first_innings.batting_team,
                "runs": match.first_innings.runs,
                "wickets": match.first_innings.wickets,
                "balls": match.first_innings.balls_faced,
                "over_summary": match.first_innings.over_summary,
            },
            {
                "team": match.second_innings.batting_team,
                "runs": match.second_innings.runs,
                "wickets": match.second_innings.wickets,
                "balls": match.second_innings.balls_faced,
                "over_summary": match.second_innings.over_summary,
            },
        ],
        "top_performers": performers,
        "ball_by_ball": [
            {
                "innings": 1,
                "over": e.over,
                "ball": e.ball_in_over,
                "striker": e.striker,
                "bowler": e.bowler,
                "outcome": e.outcome,
                "runs": e.runs,
                "score": f"{e.score_after}/{e.wickets_after}",
            }
            for e in match.first_innings.events
        ]
        + [
            {
                "innings": 2,
                "over": e.over,
                "ball": e.ball_in_over,
                "striker": e.striker,
                "bowler": e.bowler,
                "outcome": e.outcome,
                "runs": e.runs,
                "score": f"{e.score_after}/{e.wickets_after}",
            }
            for e in match.second_innings.events
        ],
    }


def simulate_once(
    db: Session,
    team1_name: str,
    team2_name: str,
    venue_name: str,
    pitch_type: str,
    humidity: float,
    dew: bool,
    seed: int | None = 42,
) -> Dict:
    team1 = get_team_by_name(db, team1_name)
    team2 = get_team_by_name(db, team2_name)
    venue = get_venue_by_name(db, venue_name)
    return _simulate_with_teams(team1, team2, venue, pitch_type, humidity, dew, seed)


def simulate_alternate_history(
    db: Session,
    team1_name: str,
    team2_name: str,
    venue_name: str,
    pitch_type: str,
    humidity: float,
    dew: bool,
    overrides: List[Dict[str, str]],
) -> Dict:
    team1 = get_team_by_name(db, team1_name)
    team2 = get_team_by_name(db, team2_name)
    venue = get_venue_by_name(db, venue_name)

    team_map = {team1.name: deepcopy(team1), team2.name: deepcopy(team2)}
    applied = []

    for ov in overrides:
        team = team_map.get(ov.get("team", ""))
        if not team:
            continue
        out_name = ov.get("out_player", "")
        in_name = ov.get("in_player", "")
        for idx, p in enumerate(team.players):
            if p.name == out_name:
                team.players[idx] = SimPlayer(
                    id=f"ah-{in_name.lower().replace(' ', '-')}",
                    name=in_name,
                    role=p.role,
                    batting=p.batting,
                    bowling=p.bowling,
                    bowling_style=p.bowling_style,
                    arm=p.arm,
                )
                applied.append({"team": team.name, "out_player": out_name, "in_player": in_name})
                break

    result = _simulate_with_teams(team_map[team1.name], team_map[team2.name], venue, pitch_type, humidity, dew, 73)
    result["overrides_applied"] = applied
    return result


def predict_match(
    db: Session,
    team1_name: str,
    team2_name: str,
    venue_name: str,
    pitch_type: str,
    humidity: float,
    dew: bool,
    runs: int,
) -> Dict:
    team1 = get_team_by_name(db, team1_name)
    team2 = get_team_by_name(db, team2_name)

    mc = run_monte_carlo(team1, team2, runs=runs)
    return summary_to_dict(mc)


def simulate_tournament(
    db: Session,
    teams: List[str],
    venue: str,
    pitch_type: str,
    humidity: float,
    dew: bool,
) -> Dict:
    table = defaultdict(lambda: {"played": 0, "won": 0, "lost": 0, "points": 0})
    fixtures = []

    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            t1, t2 = teams[i], teams[j]
            result = simulate_once(db, t1, t2, venue, pitch_type, humidity, dew, seed=i * 100 + j)
            winner = result["winner"]

            table[t1]["played"] += 1
            table[t2]["played"] += 1

            if winner == t1:
                table[t1]["won"] += 1
                table[t1]["points"] += 2
                table[t2]["lost"] += 1
            elif winner == t2:
                table[t2]["won"] += 1
                table[t2]["points"] += 2
                table[t1]["lost"] += 1
            else:
                table[t1]["points"] += 1
                table[t2]["points"] += 1

            fixtures.append({"team1": t1, "team2": t2, "winner": winner, "margin": result["margin"]})

    standings = [
        {"team": k, **v}
        for k, v in sorted(table.items(), key=lambda x: (x[1]["points"], x[1]["won"]), reverse=True)
    ]

    return {"fixtures": fixtures, "standings": standings}
