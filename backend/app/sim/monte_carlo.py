from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List

from .engine import SimulationConfig, simulate_match
from .entities import Team


@dataclass
class MonteCarloSummary:
    simulations: int
    team1_name: str
    team2_name: str
    team1_win_pct: float
    team2_win_pct: float
    tie_pct: float
    avg_team1_score: float
    avg_team2_score: float


def run_monte_carlo(team1: Team, team2: Team, runs: int = 1000) -> MonteCarloSummary:
    winners: List[str] = []
    team1_scores: List[int] = []
    team2_scores: List[int] = []

    for i in range(runs):
        config = SimulationConfig(seed=i)
        result = simulate_match(team1, team2, config)
        winners.append(result.winner)
        team1_scores.append(result.first_innings.runs)
        team2_scores.append(result.second_innings.runs)

    team1_wins = winners.count(team1.name)
    team2_wins = winners.count(team2.name)
    ties = winners.count("Tie")

    return MonteCarloSummary(
        simulations=runs,
        team1_name=team1.name,
        team2_name=team2.name,
        team1_win_pct=(team1_wins / runs) * 100,
        team2_win_pct=(team2_wins / runs) * 100,
        tie_pct=(ties / runs) * 100,
        avg_team1_score=mean(team1_scores),
        avg_team2_score=mean(team2_scores),
    )


def summary_to_dict(summary: MonteCarloSummary) -> Dict[str, float | str | int]:
    return {
        "simulations": summary.simulations,
        "team1": summary.team1_name,
        "team2": summary.team2_name,
        "team1_win_pct": round(summary.team1_win_pct, 2),
        "team2_win_pct": round(summary.team2_win_pct, 2),
        "tie_pct": round(summary.tie_pct, 2),
        "avg_team1_score": round(summary.avg_team1_score, 2),
        "avg_team2_score": round(summary.avg_team2_score, 2),
    }
