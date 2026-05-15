from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Optional

from .engine import OUTCOMES, SimulationConfig, get_phase, outcome_probabilities, pick_outcome
from .entities import BallEvent, BattingLine, BowlingLine, InningsResult, MatchResult, Player, Team


@dataclass
class MatchConditions:
    pitch_type: str = "flat"  # green, flat, dusty, slow, worn
    humidity: float = 0.4  # 0 to 1
    dew: bool = False
    boundary_size: str = "medium"  # large, medium, small


@dataclass
class TacticalState:
    batting_momentum: float = 0.0
    bowling_momentum: float = 0.0
    pressure: float = 0.0


def boundary_modifier(boundary_size: str) -> float:
    return {"large": 0.88, "medium": 1.0, "small": 1.12}.get(boundary_size, 1.0)


def pitch_modifiers(pitch_type: str) -> Dict[str, float]:
    return {
        "green": {"pace": 1.15, "spin": 0.92, "bat": 0.95},
        "flat": {"pace": 1.0, "spin": 1.0, "bat": 1.1},
        "dusty": {"pace": 0.92, "spin": 1.15, "bat": 0.96},
        "slow": {"pace": 0.95, "spin": 1.08, "bat": 0.93},
        "worn": {"pace": 0.9, "spin": 1.12, "bat": 0.9},
    }.get(pitch_type, {"pace": 1.0, "spin": 1.0, "bat": 1.0})


def choose_delivery_type(
    bowler: Player,
    phase: str,
    required_rate: float,
    wickets_in_hand: int,
) -> str:
    # Bowler AI: picks risk/reward delivery by match context.
    if phase == "death" and bowler.bowling.yorkers >= 75:
        return "yorker"
    if required_rate > 11 and bowler.bowling.variations >= 70:
        return "slower_ball"
    if wickets_in_hand <= 3 and bowler.bowling.control >= 75:
        return "wide_line"
    return "bouncer" if bowler.bowling.pace >= 80 else "hard_length"


def batter_aggression_factor(required_rate: float, wickets_in_hand: int, phase: str) -> float:
    # Batter AI: pressure pushes intent up, low wickets pulls it back.
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
    # Captain AI: attack early and when wickets are low, defend in high-risk death overs.
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
) -> Dict[str, float]:
    modified = probs.copy()

    pmods = pitch_modifiers(conditions.pitch_type)
    boundary_mult = boundary_modifier(conditions.boundary_size)

    # Venue + pitch impact on scoring shots.
    modified["4"] *= boundary_mult * pmods["bat"]
    modified["6"] *= boundary_mult * pmods["bat"]

    # Weather impact: humidity helps swing, dew reduces spin bite.
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

    # Batter intent and momentum influence attack vs risk.
    modified["4"] *= aggression_factor
    modified["6"] *= aggression_factor
    modified["wicket"] *= (0.9 + 0.2 * aggression_factor)

    # Delivery-type tactical nudges.
    if delivery_type == "yorker":
        modified["dot"] *= 1.12
        modified["wicket"] *= 1.10
        modified["6"] *= 0.85
    elif delivery_type == "slower_ball":
        modified["wicket"] *= 1.06
        modified["4"] *= 0.92
    elif delivery_type == "wide_line":
        modified["dot"] *= 1.08
        modified["6"] *= 0.86
    elif delivery_type == "bouncer":
        modified["wicket"] *= 1.04
        modified["4"] *= 0.95

    # Captain intent modifies risk profile.
    if captain_intent == "attacking":
        modified["wicket"] *= 1.08
        modified["4"] *= 1.03
        modified["6"] *= 1.03
    elif captain_intent == "defensive":
        modified["dot"] *= 1.08
        modified["4"] *= 0.95
        modified["6"] *= 0.92

    # Momentum and pressure effects for collapses/partnerships.
    modified["wicket"] *= 1.0 + max(-0.12, min(0.12, state.pressure * 0.2 - state.batting_momentum * 0.15))
    modified["4"] *= 1.0 + max(-0.12, min(0.12, state.batting_momentum * 0.18))
    modified["6"] *= 1.0 + max(-0.15, min(0.15, state.batting_momentum * 0.20))

    total = sum(max(0.001, modified[k]) for k in OUTCOMES)
    return {k: max(0.001, modified[k]) / total for k in OUTCOMES}


def update_momentum(state: TacticalState, outcome: str):
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


def simulate_innings_with_tactics(
    batting_team: Team,
    bowling_team: Team,
    config: SimulationConfig,
    conditions: MatchConditions,
    target: Optional[int] = None,
) -> InningsResult:
    rng = random.Random(config.seed)
    state = TacticalState()

    batting_order = batting_team.players
    striker_idx, non_striker_idx, next_batter_idx = 0, 1, 2

    batting_card = {p.id: BattingLine(player_id=p.id, player_name=p.name) for p in batting_order}
    bowling_card: Dict[str, BowlingLine] = {}

    total_runs = 0
    wickets = 0
    balls_faced = 0
    events: list[BallEvent] = []
    over_summary: list[str] = []

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

            base_probs = outcome_probabilities(striker, bowler, phase)
            delivery_type = choose_delivery_type(bowler, phase, required_rate, wickets_in_hand)
            aggression = batter_aggression_factor(required_rate, wickets_in_hand, phase)
            captain_intent = captain_bowling_intent(over, wickets_in_hand)

            probs = apply_tactical_modifiers(
                base_probs,
                bowler,
                state,
                conditions,
                delivery_type,
                aggression,
                captain_intent,
            )
            outcome = pick_outcome(probs, rng)
            update_momentum(state, outcome)

            bat_line = batting_card[striker.id]
            bat_line.balls += 1
            bowl_line.balls += 1
            balls_faced += 1

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

            events.append(
                BallEvent(
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
                )
            )

            if target is not None and total_runs > target:
                break

        over_summary.append(
            f"Over {over + 1}: +{total_runs - over_start_runs} runs, +{wickets - over_start_wkts} wkts | {total_runs}/{wickets}"
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
) -> MatchResult:
    config = config or SimulationConfig()
    conditions = conditions or MatchConditions()

    second_seed = (config.seed + 1) if config.seed is not None else None
    second_config = SimulationConfig(max_overs=config.max_overs, max_wickets=config.max_wickets, seed=second_seed)
    first = simulate_innings_with_tactics(team1, team2, config, conditions)
    second = simulate_innings_with_tactics(team2, team1, second_config, conditions, target=first.runs)

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
