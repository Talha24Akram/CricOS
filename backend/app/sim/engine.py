from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .entities import BallEvent, BattingLine, BowlingLine, InningsResult, MatchResult, Phase, Player, Team

OUTCOMES = ["dot", "1", "2", "3", "4", "6", "wicket"]


@dataclass
class SimulationConfig:
    max_overs: int = 20
    max_wickets: int = 10
    seed: Optional[int] = None


def get_phase(over_number: int) -> Phase:
    if over_number < 6:
        return "powerplay"
    if over_number < 15:
        return "middle"
    return "death"


def _scale(value: int) -> float:
    return max(0.0, min(1.0, value / 99.0))


def outcome_probabilities(batter: Player, bowler: Player, phase: Phase) -> Dict[str, float]:
    """Build an outcome distribution using batter skill, bowler skill, and phase context.

    The model starts from phase-specific baseline probabilities and shifts weight between
    outcomes based on ratings. This keeps probabilities interpretable and tunable.
    """
    base = {
        "powerplay": {"dot": 0.34, "1": 0.30, "2": 0.07, "3": 0.01, "4": 0.16, "6": 0.07, "wicket": 0.05},
        "middle": {"dot": 0.37, "1": 0.34, "2": 0.09, "3": 0.01, "4": 0.12, "6": 0.04, "wicket": 0.03},
        "death": {"dot": 0.28, "1": 0.29, "2": 0.08, "3": 0.01, "4": 0.18, "6": 0.12, "wicket": 0.04},
    }[phase].copy()

    bat = batter.batting
    bowl = bowler.bowling

    if bowler.bowling_style == "pace":
        handling = _scale(bat.pace_handling)
        attack_skill = (_scale(bowl.pace) + _scale(bowl.swing) + _scale(bowl.seam)) / 3.0
    else:
        handling = _scale(bat.spin_handling)
        attack_skill = _scale(bowl.spin)

    aggression = _scale(bat.aggression)
    power = _scale(bat.power)
    timing = _scale(bat.timing)
    rotation = _scale(bat.strike_rotation)
    temperament = _scale(bat.temperament)
    clutch = _scale(bat.clutch)
    death_bat = _scale(bat.death_performance)

    control = _scale(bowl.control)
    yorkers = _scale(bowl.yorkers)
    variations = _scale(bowl.variations)
    death_bowl = _scale(bowl.death_bowling)
    pressure = _scale(bowl.pressure_handling)

    boundary_boost = (power * 0.5 + timing * 0.3 + aggression * 0.2) - (control * 0.4 + attack_skill * 0.4)
    single_boost = rotation * 0.4 + timing * 0.2 - control * 0.2
    wicket_boost = (
        (attack_skill * 0.35 + variations * 0.20 + yorkers * 0.15 + pressure * 0.15 + death_bowl * 0.15)
        - (temperament * 0.35 + handling * 0.40 + clutch * 0.25)
    )

    if phase == "death":
        boundary_boost += death_bat * 0.20 - death_bowl * 0.18
        wicket_boost += death_bowl * 0.20 - death_bat * 0.15
    elif phase == "powerplay":
        boundary_boost += aggression * 0.08
        wicket_boost += attack_skill * 0.08

    base["4"] += boundary_boost * 0.08
    base["6"] += boundary_boost * 0.06
    base["1"] += single_boost * 0.08
    base["dot"] -= single_boost * 0.06
    base["wicket"] += wicket_boost * 0.08

    # Keep non-zero floor to avoid impossible events.
    probs = np.array([max(0.005, base[key]) for key in OUTCOMES], dtype=np.float64)
    probs /= probs.sum()

    return {key: float(val) for key, val in zip(OUTCOMES, probs)}


def pick_outcome(probabilities: Dict[str, float], rng: random.Random) -> str:
    threshold = rng.random()
    cumulative = 0.0
    for outcome in OUTCOMES:
        cumulative += probabilities[outcome]
        if threshold <= cumulative:
            return outcome
    return "dot"


def _choose_bowler(bowling_team: Team, over_number: int) -> Player:
    candidates = [p for p in bowling_team.players if p.role in {"bowler", "all_rounder"}]
    candidates = sorted(candidates, key=lambda p: p.bowling.control + p.bowling.death_bowling, reverse=True)
    return candidates[over_number % len(candidates)]


def _format_overs(balls: int) -> str:
    return f"{balls // 6}.{balls % 6}"


def simulate_innings(
    batting_team: Team,
    bowling_team: Team,
    config: SimulationConfig,
    target: Optional[int] = None,
) -> InningsResult:
    rng = random.Random(config.seed)

    batting_order = batting_team.players
    striker_idx = 0
    non_striker_idx = 1
    next_batter_idx = 2

    batting_card = {p.id: BattingLine(player_id=p.id, player_name=p.name) for p in batting_order}
    bowling_card: Dict[str, BowlingLine] = {}

    total_runs = 0
    wickets = 0
    balls_faced = 0
    events: List[BallEvent] = []
    over_summary: List[str] = []

    for over in range(config.max_overs):
        if wickets >= config.max_wickets:
            break

        bowler = _choose_bowler(bowling_team, over)
        bowling_line = bowling_card.setdefault(
            bowler.id,
            BowlingLine(player_id=bowler.id, player_name=bowler.name),
        )

        phase = get_phase(over)
        over_start_runs = total_runs
        over_start_wickets = wickets

        for ball_in_over in range(1, 7):
            if wickets >= config.max_wickets:
                break

            striker = batting_order[striker_idx]
            probabilities = outcome_probabilities(striker, bowler, phase)
            outcome = pick_outcome(probabilities, rng)

            bat_line = batting_card[striker.id]
            bat_line.balls += 1
            bowling_line.balls += 1
            balls_faced += 1

            ball_runs = 0
            is_wicket = False

            if outcome == "wicket":
                wickets += 1
                is_wicket = True
                bat_line.out = True
                bowling_line.wickets += 1

                if next_batter_idx < len(batting_order):
                    striker_idx = next_batter_idx
                    next_batter_idx += 1
            else:
                ball_runs = 0 if outcome == "dot" else int(outcome)
                total_runs += ball_runs
                bat_line.runs += ball_runs
                bowling_line.runs += ball_runs

                if ball_runs == 4:
                    bat_line.fours += 1
                elif ball_runs == 6:
                    bat_line.sixes += 1

                if ball_runs % 2 == 1:
                    striker_idx, non_striker_idx = non_striker_idx, striker_idx

            events.append(
                BallEvent(
                    over=over,
                    ball_in_over=ball_in_over,
                    phase=phase,
                    striker=striker.name,
                    bowler=bowler.name,
                    outcome=outcome,
                    runs=ball_runs,
                    wicket=is_wicket,
                    score_after=total_runs,
                    wickets_after=wickets,
                )
            )

            if target is not None and total_runs > target:
                break

        over_runs = total_runs - over_start_runs
        over_wkts = wickets - over_start_wickets
        over_summary.append(
            f"Over {over + 1}: +{over_runs} runs, +{over_wkts} wkts | {total_runs}/{wickets}"
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


def simulate_match(team1: Team, team2: Team, config: SimulationConfig) -> MatchResult:
    second_seed = (config.seed + 1) if config.seed is not None else None
    second_config = SimulationConfig(max_overs=config.max_overs, max_wickets=config.max_wickets, seed=second_seed)
    first = simulate_innings(team1, team2, config)
    second = simulate_innings(team2, team1, second_config, target=first.runs)

    if second.runs > first.runs:
        wickets_left = max(0, config.max_wickets - second.wickets)
        winner = team2.name
        margin = f"{wickets_left} wickets"
    elif first.runs > second.runs:
        run_margin = first.runs - second.runs
        winner = team1.name
        margin = f"{run_margin} runs"
    else:
        winner = "Tie"
        margin = "Super Over Needed"

    return MatchResult(first_innings=first, second_innings=second, winner=winner, margin=margin)


def top_performers(match: MatchResult, top_n: int = 3) -> Dict[str, List[Tuple[str, str]]]:
    batting_entries = []
    bowling_entries = []

    for innings in [match.first_innings, match.second_innings]:
        for line in innings.batting_card.values():
            if line.balls > 0:
                sr = (line.runs / line.balls) * 100
                batting_entries.append((line.player_name, line.runs, line.balls, sr))

        for line in innings.bowling_card.values():
            overs = _format_overs(line.balls)
            eco = (line.runs / (line.balls / 6)) if line.balls else 0.0
            bowling_entries.append((line.player_name, line.wickets, overs, eco))

    batting_entries.sort(key=lambda x: (x[1], x[3]), reverse=True)
    bowling_entries.sort(key=lambda x: (x[1], -x[3]), reverse=True)

    return {
        "batting": [
            (name, f"{runs} ({balls}) SR {sr:.1f}") for name, runs, balls, sr in batting_entries[:top_n]
        ],
        "bowling": [
            (name, f"{wkts}/{eco:.2f} econ in {overs} overs")
            for name, wkts, overs, eco in bowling_entries[:top_n]
        ],
    }
