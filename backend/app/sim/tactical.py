from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .engine import OUTCOMES, SimulationConfig, get_phase, outcome_probabilities, pick_outcome
from .entities import (
    BallEvent, BattingLine, BattingMindset, BowlingLine, InningsResult,
    MatchResult, Player, Team,
)


@dataclass
class MatchConditions:
    pitch_type: str = "flat"  # green, flat, dusty, slow, worn
    humidity: float = 0.4    # 0 to 1
    dew: bool = False
    boundary_size: str = "medium"  # large, medium, small


@dataclass
class TacticalState:
    batting_momentum: float = 0.0
    bowling_momentum: float = 0.0
    pressure: float = 0.0


# ── Mindset system ────────────────────────────────────────────────────────────

MINDSET_PARAMS: Dict[str, Dict[str, float]] = {
    "ultra_defensive": {"boundary_factor": 0.55, "wicket_factor": 0.55, "single_factor": 1.25},
    "defensive":       {"boundary_factor": 0.75, "wicket_factor": 0.75, "single_factor": 1.10},
    "balanced":        {"boundary_factor": 1.00, "wicket_factor": 1.00, "single_factor": 1.00},
    "aggressive":      {"boundary_factor": 1.25, "wicket_factor": 1.20, "single_factor": 0.90},
    "ultra_aggressive":{"boundary_factor": 1.55, "wicket_factor": 1.45, "single_factor": 0.80},
}


def _scale(v: int) -> float:
    return max(0.0, min(1.0, v / 99.0))


def apply_mindset_modifier(
    probs: Dict[str, float],
    batter: Player,
    mindset: str,
) -> Dict[str, float]:
    params = MINDSET_PARAMS.get(mindset, MINDSET_PARAMS["balanced"])
    modified = probs.copy()

    bf = params["boundary_factor"]
    wf = params["wicket_factor"]
    sf = params["single_factor"]

    # Natural aggression / temperament affects how well batter handles each mindset.
    nat_agg = _scale(batter.batting.aggression)
    nat_tmp = _scale(batter.batting.temperament)

    if mindset in ("aggressive", "ultra_aggressive"):
        # High-aggression batters thrive; low-aggression batters get extra wicket risk.
        agg_bonus = 1.0 + (nat_agg - 0.5) * 0.30
        bf *= agg_bonus
        wf *= 1.0 + (0.5 - nat_agg) * 0.20  # mismatch penalty
    elif mindset in ("defensive", "ultra_defensive"):
        # High-temperament batters thrive; low-temperament batters can't be passive.
        tmp_bonus = 1.0 + (nat_tmp - 0.5) * 0.20
        sf *= tmp_bonus
        wf *= max(0.5, 1.0 - (nat_tmp - 0.3) * 0.25)

    modified["4"] *= bf
    modified["6"] *= bf * 0.90
    modified["wicket"] *= wf
    modified["1"] *= sf
    modified["2"] *= sf * 0.95

    total = sum(max(0.001, modified[k]) for k in OUTCOMES)
    return {k: max(0.001, modified[k]) / total for k in OUTCOMES}


# ── Field placement system ────────────────────────────────────────────────────

# Maps each outcome to the most likely zones the ball travels to.
OUTCOME_TO_ZONES: Dict[str, List[str]] = {
    "4":       ["cover", "mid_off", "mid_on", "mid_wicket", "point", "long_on", "long_off", "deep_cover", "fine_leg"],
    "6":       ["long_on", "long_off", "deep_square_leg", "deep_cover"],
    "1":       ["mid_off", "mid_on", "mid_wicket", "square_leg", "fine_leg", "cover"],
    "2":       ["cover", "point", "mid_wicket", "mid_off"],
    "3":       ["long_on", "long_off", "deep_cover"],
    "dot":     ["slip", "gully", "point", "mid_off", "mid_on"],
    "wicket":  ["slip", "gully", "point", "mid_off", "mid_on", "fine_leg", "deep_square_leg"],
}

# SVG positions for each zone on a 600×400 oval (used by frontend)
ZONE_POSITIONS: Dict[str, List[int]] = {
    "slip":           [385, 178],
    "gully":          [422, 208],
    "point":          [468, 222],
    "cover_point":    [452, 258],
    "cover":          [415, 290],
    "mid_off":        [318, 325],
    "mid_on":         [278, 325],
    "mid_wicket":     [198, 292],
    "square_leg":     [168, 252],
    "fine_leg":       [148, 228],
    "deep_square_leg":[95, 282],
    "long_on":        [218, 372],
    "long_off":       [375, 372],
    "deep_cover":     [462, 342],
    "third_man":      [425, 162],
}

# Which zones the WK always occupies (implicit)
DEFAULT_INFIELD: List[str] = ["mid_off", "mid_on", "point", "cover", "square_leg"]


def pick_shot_zone(outcome: str, rng: random.Random) -> str:
    candidates = OUTCOME_TO_ZONES.get(outcome, ["mid_off"])
    return rng.choice(candidates)


def field_coverage_modifier(
    probs: Dict[str, float],
    field_placement: Set[str],
    outcome: str,
    shot_zone: str,
) -> Dict[str, float]:
    """Adjust probs based on whether the shot zone is covered."""
    if not field_placement:
        return probs
    modified = probs.copy()
    if shot_zone in field_placement:
        # Zone covered: more wicket/dot chance, less boundary chance
        modified["wicket"] *= 1.12
        modified["4"] *= 0.82
        modified["6"] *= 0.85
        modified["dot"] *= 1.08
    else:
        # Zone uncovered: batter can target it
        if outcome in ("4", "6"):
            modified["4"] *= 1.12
            modified["6"] *= 1.10
    total = sum(max(0.001, modified[k]) for k in OUTCOMES)
    return {k: max(0.001, modified[k]) / total for k in OUTCOMES}


# ── Delivery resolution ───────────────────────────────────────────────────────

LINE_LENGTH_MODIFIERS: Dict[str, Dict[str, Dict[str, float]]] = {
    "line": {
        "off_stump":  {"wicket": 1.08, "dot": 1.05, "4": 0.92},
        "middle":     {"wicket": 1.00, "dot": 1.00, "4": 1.00},
        "leg_stump":  {"wicket": 0.90, "1": 1.10, "4": 1.05},
        "wide":       {"dot": 1.15, "wicket": 0.85, "4": 0.88, "6": 0.85},
    },
    "length": {
        "full":         {"4": 1.10, "6": 1.08, "wicket": 1.05, "dot": 0.92},
        "good_length":  {"wicket": 1.08, "dot": 1.05},
        "short":        {"6": 1.15, "4": 1.05, "wicket": 1.08, "dot": 0.90},
        "bouncer":      {"6": 1.20, "wicket": 1.12, "dot": 1.05, "4": 0.88},
    },
    "aggression": {
        "defensive": {"dot": 1.12, "wicket": 1.06, "4": 0.88, "6": 0.85},
        "normal":    {},
        "attacking": {"wicket": 1.10, "4": 1.05, "6": 1.08, "dot": 0.92},
    },
}


def apply_line_length_modifiers(
    probs: Dict[str, float],
    line: str = "off_stump",
    length: str = "good_length",
    aggression: str = "normal",
) -> Dict[str, float]:
    modified = probs.copy()
    for category, key in [("line", line), ("length", length), ("aggression", aggression)]:
        mods = LINE_LENGTH_MODIFIERS.get(category, {}).get(key, {})
        for outcome, factor in mods.items():
            if outcome in modified:
                modified[outcome] *= factor
    total = sum(max(0.001, modified[k]) for k in OUTCOMES)
    return {k: max(0.001, modified[k]) / total for k in OUTCOMES}


def resolve_delivery(
    bowler: Player,
    phase: str,
    required_rate: float,
    wickets_in_hand: int,
    user_line: Optional[str] = None,
    user_length: Optional[str] = None,
    user_aggression: Optional[str] = None,
) -> tuple[str, str, str]:
    """Return (line, length, delivery_type) for this ball."""
    if user_line and user_length and user_aggression:
        line, length, aggr = user_line, user_length, user_aggression
    else:
        # AI logic
        line = "off_stump"
        length = "good_length"
        aggr = "normal"
        if phase == "death" and bowler.bowling.yorkers >= 75:
            length = "full"
            aggr = "attacking"
        elif required_rate > 11 and bowler.bowling.variations >= 70:
            length = "good_length"
            aggr = "defensive"
        elif wickets_in_hand <= 3 and bowler.bowling.control >= 75:
            line = "wide"
            aggr = "defensive"
        elif bowler.bowling.pace >= 80:
            length = "bouncer" if phase != "powerplay" else "short"

    # Delivery type label for BallEvent
    delivery_map = {
        ("off_stump", "full"): "yorker",
        ("off_stump", "good_length"): "seamer",
        ("middle", "good_length"): "straight",
        ("off_stump", "bouncer"): "bouncer",
        ("off_stump", "short"): "short_ball",
        ("wide", "good_length"): "wide_line",
        ("leg_stump", "full"): "inswinger",
    }
    delivery_type = delivery_map.get((line, length), "hard_length")
    return line, length, aggr, delivery_type


# ── Captain effects ───────────────────────────────────────────────────────────

def captain_bonus(captain: Optional[Player], situation: str) -> float:
    if captain is None:
        return 1.0
    base = _scale(captain.leadership.captaincy)
    reading = _scale(captain.leadership.match_reading)
    combined = (base + reading) / 2.0
    if situation == "collapse":
        return 1.0 + combined * 0.12
    if situation == "tense":
        return 1.0 + combined * 0.08
    return 1.0


def detect_situation(
    wickets: int,
    recent_wickets: int,
    runs_needed: int,
    balls_left: int,
) -> str:
    if recent_wickets >= 3:
        return "collapse"
    if runs_needed > 0 and balls_left > 0:
        rr = (runs_needed * 6) / balls_left
        if rr > 11 and wickets >= 6:
            return "tense"
    return "normal"


# ── Pitch / boundary / weather helpers (unchanged from before) ────────────────

def boundary_modifier(boundary_size: str) -> float:
    return {"large": 0.88, "medium": 1.0, "small": 1.12}.get(boundary_size, 1.0)


def pitch_modifiers(pitch_type: str) -> Dict[str, float]:
    return {
        "green": {"pace": 1.15, "spin": 0.92, "bat": 0.95},
        "flat":  {"pace": 1.0,  "spin": 1.0,  "bat": 1.1},
        "dusty": {"pace": 0.92, "spin": 1.15, "bat": 0.96},
        "slow":  {"pace": 0.95, "spin": 1.08, "bat": 0.93},
        "worn":  {"pace": 0.9,  "spin": 1.12, "bat": 0.9},
    }.get(pitch_type, {"pace": 1.0, "spin": 1.0, "bat": 1.0})


def batter_aggression_factor(required_rate: float, wickets_in_hand: int, phase: str) -> float:
    base = 1.0
    if required_rate > 10:
        base += 0.12
    if required_rate > 12:
        base += 0.08
    if wickets_in_hand <= 4:
        base -= 0.1
    if phase == "death":
        base += 0.08
    return max(0.82, min(1.25, base))


def captain_bowling_intent(over_number: int, wickets_in_hand: int) -> str:
    if over_number < 6 or wickets_in_hand <= 4:
        return "attacking"
    if over_number >= 16:
        return "defensive"
    return "balanced"


def apply_tactical_modifiers(
    probs: Dict[str, float],
    bowler: Player,
    state: TacticalState,
    conditions: MatchConditions,
    delivery_type: str,
    aggression_factor: float,
    captain_intent: str,
    field_placement: Optional[Set[str]] = None,
    shot_zone: str = "",
    mindset: str = "balanced",
    line: str = "off_stump",
    length: str = "good_length",
    bowl_aggression: str = "normal",
    cap_bonus: float = 1.0,
) -> Dict[str, float]:
    modified = probs.copy()

    pmods = pitch_modifiers(conditions.pitch_type)
    boundary_mult = boundary_modifier(conditions.boundary_size)

    # Venue + pitch impact
    modified["4"] *= boundary_mult * pmods["bat"]
    modified["6"] *= boundary_mult * pmods["bat"]

    # Weather
    if conditions.humidity > 0.65:
        modified["wicket"] *= 1.05
        modified["dot"] *= 1.03
    if conditions.dew and bowler.bowling_style == "spin":
        modified["wicket"] *= 0.92
        modified["1"] *= 1.04

    if bowler.bowling_style == "pace":
        modified["wicket"] *= pmods["pace"]
    else:
        modified["wicket"] *= pmods["spin"]

    # Batter intent
    modified["4"] *= aggression_factor
    modified["6"] *= aggression_factor
    modified["wicket"] *= (0.9 + 0.2 * aggression_factor)

    # Delivery-type tactical nudges (legacy)
    if delivery_type == "yorker":
        modified["dot"] *= 1.12
        modified["wicket"] *= 1.10
        modified["6"] *= 0.85
    elif delivery_type == "short_ball":
        modified["wicket"] *= 1.06
        modified["6"] *= 1.08
    elif delivery_type == "wide_line":
        modified["dot"] *= 1.08
        modified["6"] *= 0.86
    elif delivery_type == "bouncer":
        modified["wicket"] *= 1.04
        modified["4"] *= 0.95

    # Captain intent
    if captain_intent == "attacking":
        modified["wicket"] *= 1.08
        modified["4"] *= 1.03
        modified["6"] *= 1.03
    elif captain_intent == "defensive":
        modified["dot"] *= 1.08
        modified["4"] *= 0.95
        modified["6"] *= 0.92

    # Momentum and pressure
    modified["wicket"] *= 1.0 + max(-0.12, min(0.12, state.pressure * 0.2 - state.batting_momentum * 0.15))
    modified["4"] *= 1.0 + max(-0.12, min(0.12, state.batting_momentum * 0.18))
    modified["6"] *= 1.0 + max(-0.15, min(0.15, state.batting_momentum * 0.20))

    # Captain situational bonus (already computed externally)
    modified["wicket"] /= cap_bonus  # captain helps batters survive
    modified["dot"] /= (1.0 + (cap_bonus - 1.0) * 0.5)

    total = sum(max(0.001, modified[k]) for k in OUTCOMES)
    return {k: max(0.001, modified[k]) / total for k in OUTCOMES}


def update_momentum(state: TacticalState, outcome: str) -> None:
    if outcome in {"4", "6"}:
        state.batting_momentum = min(1.0, state.batting_momentum + 0.15)
        state.bowling_momentum = max(-1.0, state.bowling_momentum - 0.1)
    elif outcome == "wicket":
        state.batting_momentum = max(-1.0, state.batting_momentum - 0.22)
        state.bowling_momentum = min(1.0, state.bowling_momentum + 0.2)
    elif outcome == "dot":
        state.batting_momentum = max(-1.0, state.batting_momentum - 0.06)
        state.bowling_momentum = min(1.0, state.bowling_momentum + 0.05)
    else:
        state.batting_momentum *= 0.96
        state.bowling_momentum *= 0.96


def _choose_bowler(bowling_team: Team, over_number: int) -> Player:
    bowlers = [p for p in bowling_team.players if p.role in {"bowler", "all_rounder"}]
    bowlers = sorted(
        bowlers,
        key=lambda p: p.bowling.control + p.bowling.death_bowling + p.bowling.pressure_handling,
        reverse=True,
    )
    return bowlers[over_number % len(bowlers)]


# ── Tactical innings simulator ────────────────────────────────────────────────

def simulate_innings_with_tactics(
    batting_team: Team,
    bowling_team: Team,
    config: SimulationConfig,
    conditions: MatchConditions,
    target: Optional[int] = None,
    captain: Optional[Player] = None,
    # Per-batter mindset overrides: {player_id: mindset}
    mindset_map: Optional[Dict[str, str]] = None,
    # Per-ball user bowling controls (for interactive mode — list indexed by ball number)
    user_bowling_actions: Optional[List[Dict]] = None,
) -> InningsResult:
    rng = random.Random(config.seed)
    state = TacticalState()
    if mindset_map is None:
        mindset_map = {}

    batting_order = batting_team.players
    striker_idx, non_striker_idx, next_batter_idx = 0, 1, 2

    batting_card = {p.id: BattingLine(player_id=p.id, player_name=p.name) for p in batting_order}
    bowling_card: Dict[str, BowlingLine] = {}

    total_runs = 0
    wickets = 0
    balls_faced = 0
    events: list[BallEvent] = []
    over_summary: list[str] = []
    recent_wickets_tracker: list[int] = []  # last 10 balls: 1 if wicket else 0
    ball_number = 0

    for over in range(config.max_overs):
        if wickets >= config.max_wickets:
            break

        bowler = _choose_bowler(bowling_team, over)
        bowl_line = bowling_card.setdefault(
            bowler.id,
            BowlingLine(player_id=bowler.id, player_name=bowler.name),
        )

        phase = get_phase(over)
        over_start_runs = total_runs
        over_start_wkts = wickets

        for ball_in_over in range(1, 7):
            if wickets >= config.max_wickets:
                break

            striker = batting_order[striker_idx]
            runs_needed = 0 if target is None else max(0, target + 1 - total_runs)
            balls_left = max(1, 120 - balls_faced)
            required_rate = (runs_needed * 6) / balls_left if target is not None else 0.0
            wickets_in_hand = max(1, config.max_wickets - wickets)
            state.pressure = min(1.0, required_rate / 12.0) if target is not None else max(0.0, state.pressure * 0.95)

            # Mindset
            mindset = mindset_map.get(striker.id, "balanced")

            # Bowling controls
            user_action = (user_bowling_actions or [None] * 1000)[ball_number] if user_bowling_actions else None
            if user_action:
                line, length, bowl_aggr, delivery_type = resolve_delivery(
                    bowler, phase, required_rate, wickets_in_hand,
                    user_line=user_action.get("line"),
                    user_length=user_action.get("length"),
                    user_aggression=user_action.get("aggression"),
                )
            else:
                line, length, bowl_aggr, delivery_type = resolve_delivery(
                    bowler, phase, required_rate, wickets_in_hand,
                )

            aggression = batter_aggression_factor(required_rate, wickets_in_hand, phase)
            captain_intent = captain_bowling_intent(over, wickets_in_hand)

            # Captain situational bonus
            recent_wkts = sum(recent_wickets_tracker[-10:])
            situation = detect_situation(wickets, recent_wkts, runs_needed, balls_left)
            cap_b = captain_bonus(captain, situation)

            base_probs = outcome_probabilities(striker, bowler, phase)

            # Apply user field placement if provided
            shot_zone = pick_shot_zone("dot", rng)  # speculative zone for coverage check
            user_field = set(user_action.get("field_placement", [])) if user_action else set()

            probs = apply_tactical_modifiers(
                base_probs, bowler, state, conditions,
                delivery_type, aggression, captain_intent,
                field_placement=user_field,
                shot_zone=shot_zone,
                mindset=mindset,
                line=line,
                length=length,
                bowl_aggression=bowl_aggr,
                cap_bonus=cap_b,
            )

            # Apply mindset modifier
            probs = apply_mindset_modifier(probs, striker, mindset)

            # Apply line/length modifiers
            probs = apply_line_length_modifiers(probs, line, length, bowl_aggr)

            outcome = pick_outcome(probs, rng)
            actual_shot_zone = pick_shot_zone(outcome, rng)
            update_momentum(state, outcome)

            recent_wickets_tracker.append(1 if outcome == "wicket" else 0)
            if len(recent_wickets_tracker) > 20:
                recent_wickets_tracker.pop(0)

            bat_line = batting_card[striker.id]
            bat_line.balls += 1
            bowl_line.balls += 1
            balls_faced += 1
            ball_number += 1

            runs = 0
            is_wicket = False

            if outcome == "wicket":
                wickets += 1
                is_wicket = True
                bat_line.out = True
                bowl_line.wickets += 1
                if next_batter_idx < len(batting_order):
                    striker_idx = next_batter_idx
                    next_batter_idx += 1
            else:
                runs = 0 if outcome == "dot" else int(outcome)
                total_runs += runs
                bat_line.runs += runs
                bowl_line.runs += runs
                if runs == 4:
                    bat_line.fours += 1
                elif runs == 6:
                    bat_line.sixes += 1
                if runs % 2 == 1:
                    striker_idx, non_striker_idx = non_striker_idx, striker_idx

            events.append(BallEvent(
                over=over,
                ball_in_over=ball_in_over,
                phase=phase,
                striker=striker.name,
                bowler=bowler.name,
                outcome=outcome,
                runs=runs,
                wicket=is_wicket,
                score_after=total_runs,
                wickets_after=wickets,
                shot_zone=actual_shot_zone,
                delivery_type=delivery_type,
                mindset=mindset,
                striker_id=striker.id,
                bowler_id=bowler.id,
            ))

            if target is not None and total_runs > target:
                break

        over_summary.append(
            f"Over {over + 1}: +{total_runs - over_start_runs} runs, "
            f"+{wickets - over_start_wkts} wkts | {total_runs}/{wickets}"
        )
        striker_idx, non_striker_idx = non_striker_idx, striker_idx

        if target is not None and total_runs > target:
            break

    return InningsResult(
        batting_team=batting_team.name,
        bowling_team=bowling_team.name,
        runs=total_runs,
        wickets=wickets,
        balls_faced=balls_faced,
        events=events,
        batting_card=batting_card,
        bowling_card=bowling_card,
        over_summary=over_summary,
    )


def simulate_match_with_tactics(
    team1: Team,
    team2: Team,
    config: Optional[SimulationConfig] = None,
    conditions: Optional[MatchConditions] = None,
    team1_captain: Optional[Player] = None,
    team2_captain: Optional[Player] = None,
    mindset_map: Optional[Dict[str, str]] = None,
) -> MatchResult:
    config = config or SimulationConfig()
    conditions = conditions or MatchConditions()

    second_seed = (config.seed + 1) if config.seed is not None else None
    second_config = SimulationConfig(
        max_overs=config.max_overs,
        max_wickets=config.max_wickets,
        seed=second_seed,
    )

    first = simulate_innings_with_tactics(
        team1, team2, config, conditions,
        captain=team1_captain,
        mindset_map=mindset_map,
    )
    second = simulate_innings_with_tactics(
        team2, team1, second_config, conditions,
        target=first.runs,
        captain=team2_captain,
        mindset_map=mindset_map,
    )

    if second.runs > first.runs:
        winner = team2.name
        margin = f"{config.max_wickets - second.wickets} wickets"
    elif first.runs > second.runs:
        winner = team1.name
        margin = f"{first.runs - second.runs} runs"
    else:
        winner = "Tie"
        margin = "Super Over Needed"

    return MatchResult(first_innings=first, second_innings=second, winner=winner, margin=margin)
