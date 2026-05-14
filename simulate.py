from __future__ import annotations

import argparse
import json

from backend.app.sim.engine import SimulationConfig, simulate_match, top_performers
from backend.app.sim.monte_carlo import run_monte_carlo, summary_to_dict
from backend.app.sim.sample_data import build_sample_teams


def print_match_result(result) -> None:
    print("\n=== Single Match Simulation ===")
    print(
        f"{result.first_innings.batting_team}: {result.first_innings.runs}/{result.first_innings.wickets} "
        f"in {result.first_innings.balls_faced // 6}.{result.first_innings.balls_faced % 6} overs"
    )
    print(
        f"{result.second_innings.batting_team}: {result.second_innings.runs}/{result.second_innings.wickets} "
        f"in {result.second_innings.balls_faced // 6}.{result.second_innings.balls_faced % 6} overs"
    )
    print(f"Winner: {result.winner} by {result.margin}")

    print("\nOver-by-over summary (1st innings):")
    for line in result.first_innings.over_summary:
        print(f"  {line}")

    print("\nOver-by-over summary (2nd innings):")
    for line in result.second_innings.over_summary:
        print(f"  {line}")

    performers = top_performers(result)
    print("\nTop Batters:")
    for name, line in performers["batting"]:
        print(f"  {name}: {line}")

    print("\nTop Bowlers:")
    for name, line in performers["bowling"]:
        print(f"  {name}: {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CricketOS T20 simulator CLI")
    parser.add_argument("--mc", type=int, default=1000, help="Monte Carlo run count")
    parser.add_argument("--seed", type=int, default=42, help="Seed for single simulation")
    args = parser.parse_args()

    teams = build_sample_teams()
    team1, team2 = teams[0], teams[1]

    single_result = simulate_match(team1, team2, SimulationConfig(seed=args.seed))
    print_match_result(single_result)

    mc = run_monte_carlo(team1, team2, runs=args.mc)
    print("\n=== Monte Carlo Summary ===")
    print(json.dumps(summary_to_dict(mc), indent=2))


if __name__ == "__main__":
    main()
