"""Interactive game session state machine."""
from __future__ import annotations

import random
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import (
    GameSession, MatchRecord, Player, PlayerMatchStats, PlayerRating,
    Team, TeamPlayer, Venue,
)
from app.services.simulation_service import _sim_player_from_db, get_team_by_name, get_venue_by_name
from app.services.stats_service import record_match
from app.services.ratings_service import update_ratings_after_match
from app.sim.engine import (
    OUTCOMES, SimulationConfig, get_phase, outcome_probabilities, pick_outcome,
)
from app.sim.entities import (
    BallEvent, BattingLine, BowlingLine, FieldingRatings, InningsResult,
    LeadershipRatings, MatchResult, Player as SimPlayer, Team as SimTeam, WKRatings,
)
from app.sim.tactical import (
    MatchConditions, TacticalState, apply_line_length_modifiers, apply_mindset_modifier,
    apply_tactical_modifiers, batter_aggression_factor, captain_bonus, captain_bowling_intent,
    detect_situation, field_coverage_modifier, pick_shot_zone, resolve_delivery,
    simulate_match_with_tactics, update_momentum,
)


# ─── DB helpers ───────────────────────────────────────────────────────────────

def _load_sim_players(db: Session, player_ids: List[int]) -> Dict[int, SimPlayer]:
    players = db.execute(select(Player).where(Player.id.in_(player_ids))).scalars().all()
    ratings = db.execute(
        select(PlayerRating).where(
            PlayerRating.player_id.in_(player_ids),
            PlayerRating.version == "latest",
        )
    ).scalars().all()
    rating_map = {r.player_id: r for r in ratings}
    return {p.id: _sim_player_from_db(p, rating_map.get(p.id)) for p in players}


def _get_session(db: Session, session_id: str) -> GameSession:
    s = db.execute(select(GameSession).where(GameSession.id == session_id)).scalar_one_or_none()
    if s is None:
        raise ValueError(f"Session not found: {session_id}")
    return s


def _default_lineup(db: Session, team_name: str) -> Tuple[List[int], int, int]:
    """Return (player_ids[11], captain_id, wk_id) from DB for AI-picked squad."""
    team = db.execute(select(Team).where(Team.name == team_name)).scalar_one_or_none()
    if team is None:
        raise ValueError(f"Team not found: {team_name}")
    links = db.execute(
        select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.is_active.is_(True))
    ).scalars().all()
    pids = [l.player_id for l in links][:11]
    players = db.execute(select(Player).where(Player.id.in_(pids))).scalars().all()
    p_map = {p.id: p for p in players}

    wk_id = next(
        (pid for pid in pids if p_map.get(pid) and p_map[pid].role == "wicket_keeper"),
        pids[6] if len(pids) > 6 else pids[-1],
    )
    captain_id = pids[0]
    return pids, captain_id, wk_id


# ─── Core ball simulation ─────────────────────────────────────────────────────

def _simulate_one_ball(
    striker: SimPlayer,
    bowler: SimPlayer,
    over: int,
    conditions: MatchConditions,
    tactical_state: TacticalState,
    rng: random.Random,
    mindset: str = "balanced",
    field_placement: Optional[Set[str]] = None,
    bowl_line: Optional[str] = None,
    bowl_length: Optional[str] = None,
    bowl_aggression: Optional[str] = None,
    target: Optional[int] = None,
    score: int = 0,
    wickets: int = 0,
    balls: int = 0,
    captain: Optional[SimPlayer] = None,
    recent_wickets: Optional[List[int]] = None,
) -> Tuple[str, str, str, str, str, str]:
    """Return (outcome, shot_zone, delivery_type, line, length, aggr)."""
    phase = get_phase(over)
    wickets_in_hand = max(1, 10 - wickets)
    runs_needed = max(0, target + 1 - score) if target is not None else 0
    balls_left = max(1, 120 - balls)
    required_rate = (runs_needed * 6) / balls_left if target is not None else 0.0

    line, length, aggr, delivery_type = resolve_delivery(
        bowler, phase, required_rate, wickets_in_hand,
        user_line=bowl_line, user_length=bowl_length, user_aggression=bowl_aggression,
    )

    aggression_factor = batter_aggression_factor(required_rate, wickets_in_hand, phase)
    cap_intent = captain_bowling_intent(over, wickets_in_hand)

    recent_wkts = sum((recent_wickets or [])[-10:])
    situation = detect_situation(wickets, recent_wkts, runs_needed, balls_left)
    cap_b = captain_bonus(captain, situation)

    shot_zone_speculative = pick_shot_zone("dot", rng)
    field = field_placement or set()

    base_probs = outcome_probabilities(striker, bowler, phase)
    probs = apply_tactical_modifiers(
        base_probs, bowler, tactical_state, conditions,
        delivery_type, aggression_factor, cap_intent,
        field_placement=field,
        shot_zone=shot_zone_speculative,
        mindset=mindset,
        line=line,
        length=length,
        bowl_aggression=aggr,
        cap_bonus=cap_b,
    )
    probs = apply_mindset_modifier(probs, striker, mindset)
    probs = apply_line_length_modifiers(probs, line, length, aggr)

    outcome = pick_outcome(probs, rng)
    actual_zone = pick_shot_zone(outcome, rng)
    update_momentum(tactical_state, outcome)

    return outcome, actual_zone, delivery_type, line, length, aggr


# ─── Session creation ─────────────────────────────────────────────────────────

def create_session(
    db: Session,
    mode: str,
    team1: str,
    team2: str,
    venue: str,
    pitch_type: str = "flat",
    humidity: float = 0.4,
    dew: bool = False,
) -> GameSession:
    session = GameSession(
        mode=mode,
        status="setup",
        team1_name=team1,
        team2_name=team2,
        venue_name=venue,
        pitch_type=pitch_type,
        humidity=humidity,
        dew=dew,
        game_state={"status": "setup", "pending_action": "set_lineup"},
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # For ai_vs_ai / quicksim: auto-set lineups and jump straight to toss
    if mode in ("ai_vs_ai", "quicksim"):
        _auto_set_lineups(db, session)

    return session


def _auto_set_lineups(db: Session, session: GameSession) -> None:
    t1_pids, t1_cap, t1_wk = _default_lineup(db, session.team1_name)
    t2_pids, t2_cap, t2_wk = _default_lineup(db, session.team2_name)
    session.team1_lineup = t1_pids
    session.team2_lineup = t2_pids
    session.team1_captain_id = t1_cap
    session.team2_captain_id = t2_cap
    session.team1_wk_id = t1_wk
    session.team2_wk_id = t2_wk
    gs = dict(session.game_state)
    gs["status"] = "toss"
    gs["pending_action"] = "toss_decision"
    session.game_state = gs
    session.status = "toss"
    db.commit()


# ─── State response ───────────────────────────────────────────────────────────

def get_state(db: Session, session_id: str) -> Dict:
    session = _get_session(db, session_id)
    return _build_response(session)


def _build_response(session: GameSession) -> Dict:
    gs = session.game_state or {}
    return {
        "session_id": session.id,
        "mode": session.mode,
        "status": session.status,
        "team1": session.team1_name,
        "team2": session.team2_name,
        "venue": session.venue_name,
        "pitch_type": session.pitch_type,
        "pending_action": gs.get("pending_action"),
        "innings": gs.get("innings", 1),
        "batting_team": gs.get("batting_team"),
        "bowling_team": gs.get("bowling_team"),
        "score": gs.get("score", 0),
        "wickets": gs.get("wickets", 0),
        "balls": gs.get("balls", 0),
        "target": gs.get("target"),
        "striker_id": gs.get("striker_id"),
        "non_striker_id": gs.get("non_striker_id"),
        "next_batter_idx": gs.get("next_batter_idx", 2),
        "current_bowler_id": gs.get("current_bowler_id"),
        "batting_card": gs.get("batting_card", {}),
        "bowling_card": gs.get("bowling_card", {}),
        "events": (gs.get("events") or [])[-30:],
        "over_summary": gs.get("over_summary", []),
        "last_ball": gs.get("last_ball"),
        "user_controls_batting": gs.get("user_controls_batting"),
        "user_controls_bowling": gs.get("user_controls_bowling"),
        "mindset_map": gs.get("mindset_map", {}),
        "team1_lineup": session.team1_lineup or [],
        "team2_lineup": session.team2_lineup or [],
        "team1_captain_id": session.team1_captain_id,
        "team2_captain_id": session.team2_captain_id,
        "team1_wk_id": session.team1_wk_id,
        "team2_wk_id": session.team2_wk_id,
        "toss_winner": session.toss_winner,
        "toss_decision": session.toss_decision,
        "winner": gs.get("winner"),
        "margin": gs.get("margin"),
        "innings1": gs.get("innings1"),
        "innings2": gs.get("innings2"),
    }


# ─── Action dispatcher ────────────────────────────────────────────────────────

def post_action(db: Session, session_id: str, action_type: str, payload: Dict) -> Dict:
    session = _get_session(db, session_id)
    gs = dict(session.game_state or {})

    if action_type == "set_lineup":
        _handle_set_lineup(db, session, gs, payload)
    elif action_type == "toss_decision":
        _handle_toss(db, session, gs, payload)
    elif action_type == "set_mindset":
        _handle_set_mindset(gs, payload)
    elif action_type == "sim_ball":
        _handle_sim_ball(db, session, gs, payload)
    elif action_type == "sim_over":
        _handle_sim_over(db, session, gs)
    elif action_type == "bowl":
        _handle_bowl(db, session, gs, payload)
    elif action_type == "select_batter":
        _handle_select_batter(db, session, gs, payload)
    elif action_type == "start_innings2":
        _start_innings2(db, session, gs)
    else:
        raise ValueError(f"Unknown action: {action_type}")

    session.game_state = {**gs}
    session.status = gs.get("status", session.status)
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    if gs.get("status") == "completed":
        _finalize_match(db, session, gs)

    return _build_response(session)


# ─── Action handlers ──────────────────────────────────────────────────────────

def _handle_set_lineup(db: Session, session: GameSession, gs: Dict, payload: Dict) -> None:
    team = payload.get("team", "team1")
    player_ids = [int(x) for x in payload.get("player_ids", [])][:11]
    captain_id = int(payload["captain_id"]) if payload.get("captain_id") else player_ids[0]
    wk_id = int(payload["wk_id"]) if payload.get("wk_id") else player_ids[-1]

    if team == "team1":
        session.team1_lineup = player_ids
        session.team1_captain_id = captain_id
        session.team1_wk_id = wk_id

        if session.mode == "user_vs_ai":
            # Auto-pick team2 lineup
            t2_pids, t2_cap, t2_wk = _default_lineup(db, session.team2_name)
            session.team2_lineup = t2_pids
            session.team2_captain_id = t2_cap
            session.team2_wk_id = t2_wk
            gs["status"] = "toss"
            gs["pending_action"] = "toss_decision"
            session.status = "toss"
        else:
            gs["pending_action"] = "set_lineup_team2"

    elif team == "team2":
        session.team2_lineup = player_ids
        session.team2_captain_id = captain_id
        session.team2_wk_id = wk_id
        gs["status"] = "toss"
        gs["pending_action"] = "toss_decision"
        session.status = "toss"


def _handle_toss(db: Session, session: GameSession, gs: Dict, payload: Dict) -> None:
    """Resolve toss and start innings 1."""
    toss_winner = payload.get("toss_winner") or session.team1_name
    decision = payload.get("decision", "bat")

    session.toss_winner = toss_winner
    session.toss_decision = decision

    if decision == "bat":
        batting_team = toss_winner
        bowling_team = session.team2_name if toss_winner == session.team1_name else session.team1_name
    else:
        bowling_team = toss_winner
        batting_team = session.team2_name if toss_winner == session.team1_name else session.team1_name

    # In user_vs_ai, team1 = user's team. Control depends on batting/bowling assignment.
    if session.mode in ("ai_vs_ai", "quicksim"):
        user_batting = False
        user_bowling = False
    elif session.mode == "user_vs_ai":
        user_batting = (batting_team == session.team1_name)
        user_bowling = (bowling_team == session.team1_name)
    else:  # user_vs_user
        user_batting = True
        user_bowling = True

    gs.update({
        "status": "innings1",
        "innings": 1,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "user_controls_batting": user_batting,
        "user_controls_bowling": user_bowling,
    })
    session.status = "innings1"

    _init_innings(db, session, gs, innings_num=1)

    # If no user input needed, auto-simulate now
    if not user_batting and not user_bowling:
        _auto_simulate_innings(db, session, gs)


def _init_innings(db: Session, session: GameSession, gs: Dict, innings_num: int) -> None:
    """Set up all the state for a new innings."""
    batting_team = gs["batting_team"]
    is_team1_batting = (batting_team == session.team1_name)

    batting_lineup = session.team1_lineup if is_team1_batting else session.team2_lineup
    bowling_lineup = session.team2_lineup if is_team1_batting else session.team1_lineup
    batting_captain_id = session.team1_captain_id if is_team1_batting else session.team2_captain_id
    bowling_captain_id = session.team2_captain_id if is_team1_batting else session.team1_captain_id

    if not batting_lineup or not bowling_lineup:
        raise ValueError("Lineups not set — cannot start innings")

    # Load player names for cards
    all_pids = list(set(batting_lineup + bowling_lineup))
    players = db.execute(select(Player).where(Player.id.in_(all_pids))).scalars().all()
    name_map = {p.id: p.name for p in players}

    batting_card = {
        str(pid): {
            "player_id": pid,
            "player_name": name_map.get(pid, f"Player {pid}"),
            "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False,
        }
        for pid in batting_lineup
    }

    # Initial bowler
    first_bowler_id = _pick_bowler_id(bowling_lineup, players, over=0, bowling_card={})

    gs.update({
        "innings": innings_num,
        "score": 0,
        "wickets": 0,
        "balls": 0,
        "ball_number": 0,
        "batting_lineup": batting_lineup,
        "bowling_lineup": bowling_lineup,
        "batting_captain_id": batting_captain_id,
        "bowling_captain_id": bowling_captain_id,
        "striker_idx": 0,
        "non_striker_idx": 1,
        "next_batter_idx": 2,
        "striker_id": batting_lineup[0],
        "non_striker_id": batting_lineup[1] if len(batting_lineup) > 1 else batting_lineup[0],
        "current_bowler_id": first_bowler_id,
        "batting_card": batting_card,
        "bowling_card": {},
        "events": [],
        "over_summary": [],
        "last_ball": None,
        "mindset_map": {},
        "recent_wickets": [],
        "tactical_state": {"batting_momentum": 0.0, "bowling_momentum": 0.0, "pressure": 0.0},
    })

    _set_next_pending_action(gs)


def _set_next_pending_action(gs: Dict) -> None:
    user_batting = gs.get("user_controls_batting", False)
    user_bowling = gs.get("user_controls_bowling", False)

    if user_batting:
        gs["pending_action"] = "batting_decision"
    elif user_bowling:
        gs["pending_action"] = "bowling_decision"
    else:
        gs["pending_action"] = "auto"


def _pick_bowler_id(lineup: List[int], players: List[Player], over: int, bowling_card: Dict) -> int:
    p_map = {p.id: p for p in players}
    candidates = []
    for pid in lineup:
        p = p_map.get(pid)
        if p and p.role in ("bowler", "all_rounder"):
            overs_done = bowling_card.get(str(pid), {}).get("balls", 0) // 6
            if overs_done < 4:
                candidates.append(pid)

    if not candidates:
        candidates = [pid for pid in lineup if bowling_card.get(str(pid), {}).get("balls", 0) // 6 < 4]
    if not candidates:
        candidates = lineup

    return candidates[over % len(candidates)]


def _pick_bowler_id_from_db(db: Session, lineup: List[int], over: int, bowling_card: Dict) -> int:
    players = db.execute(select(Player).where(Player.id.in_(lineup))).scalars().all()
    return _pick_bowler_id(lineup, players, over, bowling_card)


# ─── Auto-simulate (AI vs AI, or AI innings in user_vs_ai) ────────────────────

def _auto_simulate_innings(db: Session, session: GameSession, gs: Dict) -> None:
    """Simulate the current entire innings automatically (no user input)."""
    batting_lineup = gs["batting_lineup"]
    bowling_lineup = gs["bowling_lineup"]

    # Load players and build SimTeam objects
    all_pids = list(set(batting_lineup + bowling_lineup))
    sim_map = _load_sim_players(db, all_pids)

    bat_team = SimTeam(
        id=str(gs["innings"]),
        name=gs["batting_team"],
        players=[sim_map[pid] for pid in batting_lineup if pid in sim_map],
    )
    bowl_team = SimTeam(
        id=str(gs["innings"] + 10),
        name=gs["bowling_team"],
        players=[sim_map[pid] for pid in bowling_lineup if pid in sim_map],
    )

    venue = db.execute(select(Venue).where(Venue.name == session.venue_name)).scalar_one_or_none()
    conditions = MatchConditions(
        pitch_type=session.pitch_type,
        humidity=session.humidity,
        dew=session.dew,
        boundary_size=venue.boundary_size if venue else "medium",
    )

    batting_cap_id = gs.get("batting_captain_id")
    batting_cap = sim_map.get(batting_cap_id) if batting_cap_id else None

    seed = 42 + gs.get("innings", 1) * 1000
    cfg = SimulationConfig(seed=seed)
    target = gs.get("target")

    from app.sim.tactical import simulate_innings_with_tactics
    result = simulate_innings_with_tactics(
        bat_team, bowl_team, cfg, conditions,
        target=target,
        captain=batting_cap,
        mindset_map=gs.get("mindset_map"),
    )

    _store_innings_result(gs, result)


def _store_innings_result(gs: Dict, result: InningsResult) -> None:
    """Write innings result into the game state and transition to next status."""
    innings_num = gs.get("innings", 1)

    # Flatten cards for JSON storage
    batting_card_json = {
        pid: {
            "player_id": line.player_id, "player_name": line.player_name,
            "runs": line.runs, "balls": line.balls,
            "fours": line.fours, "sixes": line.sixes, "out": line.out,
        }
        for pid, line in result.batting_card.items()
    }
    bowling_card_json = {
        pid: {
            "player_id": line.player_id, "player_name": line.player_name,
            "balls": line.balls, "runs": line.runs, "wickets": line.wickets,
        }
        for pid, line in result.bowling_card.items()
    }
    events_json = [
        {
            "over": e.over, "ball": e.ball_in_over, "innings": innings_num,
            "striker": e.striker, "bowler": e.bowler,
            "outcome": e.outcome, "runs": e.runs, "wicket": e.wicket,
            "score_after": e.score_after, "wickets_after": e.wickets_after,
            "shot_zone": e.shot_zone, "delivery_type": e.delivery_type,
            "mindset": e.mindset,
            "striker_id": e.striker_id, "bowler_id": e.bowler_id,
        }
        for e in result.events
    ]

    innings_summary = {
        "batting_team": result.batting_team,
        "bowling_team": result.bowling_team,
        "runs": result.runs,
        "wickets": result.wickets,
        "balls": result.balls_faced,
        "over_summary": result.over_summary,
        "batting_card": batting_card_json,
        "bowling_card": bowling_card_json,
    }

    if innings_num == 1:
        gs["innings1"] = innings_summary
        gs["innings1_score"] = result.runs
        gs["score"] = result.runs
        gs["wickets"] = result.wickets
        gs["balls"] = result.balls_faced
        gs["batting_card"] = batting_card_json
        gs["bowling_card"] = bowling_card_json
        gs["events"] = events_json
        gs["over_summary"] = result.over_summary
        gs["status"] = "innings1_done"
        gs["pending_action"] = "start_innings2"
    else:
        gs["innings2"] = innings_summary
        gs["score"] = result.runs
        gs["wickets"] = result.wickets
        gs["balls"] = result.balls_faced
        gs["batting_card"] = batting_card_json
        gs["bowling_card"] = bowling_card_json
        gs["events"] = events_json
        gs["over_summary"] = result.over_summary
        _finalize_result(gs)


def _finalize_result(gs: Dict) -> None:
    i1 = gs.get("innings1", {})
    i2 = gs.get("innings2", {})
    score1 = i1.get("runs", 0)
    score2 = i2.get("runs", 0)
    wickets2 = i2.get("wickets", 0)

    if score2 > score1:
        gs["winner"] = i2.get("batting_team", "Team 2")
        gs["margin"] = f"{10 - wickets2} wickets"
    elif score1 > score2:
        gs["winner"] = i1.get("batting_team", "Team 1")
        gs["margin"] = f"{score1 - score2} runs"
    else:
        gs["winner"] = "Tie"
        gs["margin"] = "Super Over Needed"

    gs["status"] = "completed"
    gs["pending_action"] = "review"


# ─── Interactive ball simulation ──────────────────────────────────────────────

def _get_conditions_and_players(
    db: Session, session: GameSession, gs: Dict
) -> Tuple[MatchConditions, Dict[int, SimPlayer]]:
    venue = db.execute(select(Venue).where(Venue.name == session.venue_name)).scalar_one_or_none()
    conditions = MatchConditions(
        pitch_type=session.pitch_type,
        humidity=session.humidity,
        dew=session.dew,
        boundary_size=venue.boundary_size if venue else "medium",
    )
    all_pids = list(set(gs.get("batting_lineup", []) + gs.get("bowling_lineup", [])))
    sim_map = _load_sim_players(db, all_pids)
    return conditions, sim_map


def _restore_tactical_state(gs: Dict) -> TacticalState:
    ts = gs.get("tactical_state", {})
    return TacticalState(
        batting_momentum=ts.get("batting_momentum", 0.0),
        bowling_momentum=ts.get("bowling_momentum", 0.0),
        pressure=ts.get("pressure", 0.0),
    )


def _save_tactical_state(gs: Dict, ts: TacticalState) -> None:
    gs["tactical_state"] = {
        "batting_momentum": ts.batting_momentum,
        "bowling_momentum": ts.bowling_momentum,
        "pressure": ts.pressure,
    }


def _apply_ball_result(
    gs: Dict,
    outcome: str,
    shot_zone: str,
    delivery_type: str,
    line: str,
    length: str,
    mindset: str,
    striker_id: int,
    bowler_id: int,
    striker_name: str,
    bowler_name: str,
) -> None:
    over = gs["balls"] // 6
    ball_in_over = (gs["balls"] % 6) + 1
    phase = get_phase(over)

    batting_card = gs["batting_card"]
    bowling_card = gs["bowling_card"]

    bat_key = str(striker_id)
    bowl_key = str(bowler_id)

    if bat_key not in batting_card:
        batting_card[bat_key] = {
            "player_id": striker_id, "player_name": striker_name,
            "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False,
        }
    if bowl_key not in bowling_card:
        bowling_card[bowl_key] = {
            "player_id": bowler_id, "player_name": bowler_name,
            "balls": 0, "runs": 0, "wickets": 0,
        }

    batting_card[bat_key]["balls"] += 1
    bowling_card[bowl_key]["balls"] += 1
    gs["balls"] += 1
    gs["ball_number"] = gs.get("ball_number", 0) + 1

    runs = 0
    is_wicket = False

    if outcome == "wicket":
        is_wicket = True
        batting_card[bat_key]["out"] = True
        bowling_card[bowl_key]["wickets"] += 1
        gs["wickets"] += 1
    else:
        runs = 0 if outcome == "dot" else int(outcome)
        gs["score"] += runs
        batting_card[bat_key]["runs"] += runs
        bowling_card[bowl_key]["runs"] += runs
        if runs == 4:
            batting_card[bat_key]["fours"] += 1
        elif runs == 6:
            batting_card[bat_key]["sixes"] += 1
        if runs % 2 == 1:
            si = gs["striker_idx"]
            ni = gs["non_striker_idx"]
            gs["striker_idx"] = ni
            gs["non_striker_idx"] = si

    # Update recent wickets
    rw = gs.get("recent_wickets", [])
    rw.append(1 if is_wicket else 0)
    if len(rw) > 20:
        rw = rw[-20:]
    gs["recent_wickets"] = rw

    # Store event
    event = {
        "over": over, "ball": ball_in_over, "innings": gs.get("innings", 1),
        "striker": striker_name, "bowler": bowler_name,
        "striker_id": str(striker_id), "bowler_id": str(bowler_id),
        "outcome": outcome, "runs": runs, "wicket": is_wicket,
        "score_after": gs["score"], "wickets_after": gs["wickets"],
        "shot_zone": shot_zone, "delivery_type": delivery_type,
        "mindset": mindset, "phase": phase,
    }
    gs.setdefault("events", []).append(event)
    gs["last_ball"] = event

    # Over summary
    if ball_in_over == 6 or (gs["wickets"] >= 10):
        over_events = [e for e in gs["events"] if e["over"] == over]
        over_runs = sum(e["runs"] for e in over_events)
        over_wkts = sum(1 for e in over_events if e["wicket"])
        gs.setdefault("over_summary", []).append(
            f"Over {over + 1}: +{over_runs} runs, +{over_wkts} wkts | {gs['score']}/{gs['wickets']}"
        )


def _advance_post_ball(db: Session, session: GameSession, gs: Dict) -> None:
    """After a ball is resolved, update batters/bowler and set next pending action."""
    batting_lineup = gs["batting_lineup"]
    bowling_lineup = gs["bowling_lineup"]
    balls = gs["balls"]
    over = (balls - 1) // 6  # the over we just completed a ball in
    ball_in_over = balls % 6  # 0 means just completed an over

    target = gs.get("target")
    score = gs["score"]
    wickets = gs["wickets"]

    # Check innings over
    innings_done = wickets >= 10 or balls >= 120 or (target is not None and score > target)
    if innings_done:
        _end_innings(db, session, gs)
        return

    # Wicket — need new batter
    if gs["last_ball"]["wicket"]:
        next_idx = gs.get("next_batter_idx", 2)
        if next_idx < len(batting_lineup):
            gs["striker_idx"] = next_idx
            gs["next_batter_idx"] = next_idx + 1
            gs["striker_id"] = batting_lineup[gs["striker_idx"]]
        # User may want to choose the batter
        if gs.get("user_controls_batting"):
            gs["pending_action"] = "select_batter"
            return

    # Update striker_id / non_striker_id from indices
    si = gs["striker_idx"]
    ni = gs["non_striker_idx"]
    if si < len(batting_lineup):
        gs["striker_id"] = batting_lineup[si]
    if ni < len(batting_lineup):
        gs["non_striker_id"] = batting_lineup[ni]

    # End of over — swap ends + pick new bowler
    if ball_in_over == 0:
        gs["striker_idx"], gs["non_striker_idx"] = gs["non_striker_idx"], gs["striker_idx"]
        gs["striker_id"], gs["non_striker_id"] = gs["non_striker_id"], gs["striker_id"]
        new_over = balls // 6
        gs["current_bowler_id"] = _pick_bowler_id_from_db(
            db, bowling_lineup, new_over, gs["bowling_card"]
        )

    _set_next_pending_action(gs)


def _end_innings(db: Session, session: GameSession, gs: Dict) -> None:
    innings_num = gs.get("innings", 1)
    innings_summary = {
        "batting_team": gs["batting_team"],
        "bowling_team": gs["bowling_team"],
        "runs": gs["score"],
        "wickets": gs["wickets"],
        "balls": gs["balls"],
        "over_summary": gs.get("over_summary", []),
        "batting_card": gs.get("batting_card", {}),
        "bowling_card": gs.get("bowling_card", {}),
    }

    if innings_num == 1:
        gs["innings1"] = innings_summary
        gs["innings1_score"] = gs["score"]
        gs["status"] = "innings1_done"
        gs["pending_action"] = "start_innings2"
    else:
        gs["innings2"] = innings_summary
        _finalize_result(gs)


def _handle_sim_ball(db: Session, session: GameSession, gs: Dict, payload: Dict) -> None:
    if gs.get("pending_action") not in ("batting_decision", "auto"):
        return

    conditions, sim_map = _get_conditions_and_players(db, session, gs)
    ts = _restore_tactical_state(gs)

    striker_id = gs["striker_id"]
    bowler_id = gs["current_bowler_id"]
    striker = sim_map.get(striker_id)
    bowler = sim_map.get(bowler_id)
    if striker is None or bowler is None:
        return

    mindset = gs.get("mindset_map", {}).get(str(striker_id), "balanced")
    over = gs["balls"] // 6
    rng = random.Random(42 + gs.get("ball_number", 0) + session.id.__hash__() % 1000)

    outcome, shot_zone, delivery_type, line, length, aggr = _simulate_one_ball(
        striker, bowler, over, conditions, ts,
        rng, mindset=mindset,
        target=gs.get("target"), score=gs["score"],
        wickets=gs["wickets"], balls=gs["balls"],
        captain=sim_map.get(gs.get("bowling_captain_id")),
        recent_wickets=gs.get("recent_wickets"),
    )

    _save_tactical_state(gs, ts)
    _apply_ball_result(
        gs, outcome, shot_zone, delivery_type, line, length, mindset,
        striker_id, bowler_id, striker.name, bowler.name,
    )
    _advance_post_ball(db, session, gs)


def _handle_sim_over(db: Session, session: GameSession, gs: Dict) -> None:
    for _ in range(6):
        if gs.get("pending_action") not in ("batting_decision", "auto"):
            break
        if gs.get("status") in ("innings1_done", "completed"):
            break
        _handle_sim_ball(db, session, gs, {})


def _handle_bowl(db: Session, session: GameSession, gs: Dict, payload: Dict) -> None:
    if gs.get("pending_action") != "bowling_decision":
        return

    conditions, sim_map = _get_conditions_and_players(db, session, gs)
    ts = _restore_tactical_state(gs)

    striker_id = gs["striker_id"]
    bowler_id = gs["current_bowler_id"]
    striker = sim_map.get(striker_id)
    bowler = sim_map.get(bowler_id)
    if striker is None or bowler is None:
        return

    field = set(payload.get("field_placement", []))
    bowl_line = payload.get("line")
    bowl_length = payload.get("length")
    bowl_aggr = payload.get("aggression")

    # Batter mindset chosen by AI when user is bowling
    mindset = "balanced"
    over = gs["balls"] // 6
    rng = random.Random(42 + gs.get("ball_number", 0) + session.id.__hash__() % 1000)

    outcome, shot_zone, delivery_type, line, length, aggr = _simulate_one_ball(
        striker, bowler, over, conditions, ts,
        rng, mindset=mindset,
        field_placement=field,
        bowl_line=bowl_line, bowl_length=bowl_length, bowl_aggression=bowl_aggr,
        target=gs.get("target"), score=gs["score"],
        wickets=gs["wickets"], balls=gs["balls"],
        captain=sim_map.get(gs.get("batting_captain_id")),
        recent_wickets=gs.get("recent_wickets"),
    )

    _save_tactical_state(gs, ts)
    _apply_ball_result(
        gs, outcome, shot_zone, delivery_type, line, length, mindset,
        striker_id, bowler_id, striker.name, bowler.name,
    )
    _advance_post_ball(db, session, gs)


def _handle_set_mindset(gs: Dict, payload: Dict) -> None:
    player_id = str(payload.get("player_id", ""))
    mindset = payload.get("mindset", "balanced")
    if player_id:
        gs.setdefault("mindset_map", {})[player_id] = mindset


def _handle_select_batter(db: Session, session: GameSession, gs: Dict, payload: Dict) -> None:
    player_id = int(payload.get("player_id", 0))
    batting_lineup = gs.get("batting_lineup", [])

    if player_id in batting_lineup:
        idx = batting_lineup.index(player_id)
        gs["striker_idx"] = idx
        gs["striker_id"] = player_id

    _set_next_pending_action(gs)


def _start_innings2(db: Session, session: GameSession, gs: Dict) -> None:
    """Swap sides and initialise innings 2."""
    # In innings 2, the teams swap batting/bowling
    batting_team = gs["bowling_team"]  # was bowling, now batting
    bowling_team = gs["batting_team"]  # was batting, now bowling

    gs["batting_team"] = batting_team
    gs["bowling_team"] = bowling_team
    gs["target"] = gs.get("innings1_score", 0)
    gs["status"] = "innings2"

    # Determine user controls for innings 2
    if session.mode in ("ai_vs_ai", "quicksim"):
        gs["user_controls_batting"] = False
        gs["user_controls_bowling"] = False
    elif session.mode == "user_vs_ai":
        user_batting = (batting_team == session.team1_name)
        gs["user_controls_batting"] = user_batting
        gs["user_controls_bowling"] = not user_batting
    else:
        gs["user_controls_batting"] = True
        gs["user_controls_bowling"] = True

    session.status = "innings2"
    _init_innings(db, session, gs, innings_num=2)

    if not gs.get("user_controls_batting") and not gs.get("user_controls_bowling"):
        _auto_simulate_innings(db, session, gs)


# ─── Match finalisation ───────────────────────────────────────────────────────

def _finalize_match(db: Session, session: GameSession, gs: Dict) -> None:
    """Persist match record and update player ratings."""
    # Build InningsResult objects from stored JSON
    i1_data = gs.get("innings1", {})
    i2_data = gs.get("innings2", {})
    if not i1_data or not i2_data:
        return

    def _rebuild_innings(data: Dict) -> InningsResult:
        batting_card = {
            k: BattingLine(
                player_id=v["player_id"], player_name=v["player_name"],
                runs=v["runs"], balls=v["balls"],
                fours=v["fours"], sixes=v["sixes"], out=v["out"],
            )
            for k, v in data.get("batting_card", {}).items()
        }
        bowling_card = {
            k: BowlingLine(
                player_id=v["player_id"], player_name=v["player_name"],
                balls=v["balls"], runs=v["runs"], wickets=v["wickets"],
            )
            for k, v in data.get("bowling_card", {}).items()
        }
        return InningsResult(
            batting_team=data["batting_team"],
            bowling_team=data["bowling_team"],
            runs=data["runs"],
            wickets=data["wickets"],
            balls_faced=data["balls"],
            events=[],
            batting_card=batting_card,
            bowling_card=bowling_card,
            over_summary=data.get("over_summary", []),
        )

    match = MatchResult(
        first_innings=_rebuild_innings(i1_data),
        second_innings=_rebuild_innings(i2_data),
        winner=gs.get("winner", ""),
        margin=gs.get("margin", ""),
    )

    try:
        match_record = record_match(db, session, match)
        all_stats = db.execute(
            select(PlayerMatchStats).where(PlayerMatchStats.match_id == match_record.id)
        ).scalars().all()
        update_ratings_after_match(db, all_stats)
    except Exception:
        pass  # Don't crash the response if finalisation fails
