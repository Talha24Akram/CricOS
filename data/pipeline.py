from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import delete, select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.models.tables import BatterBowlerMatchup, Player, PlayerRating, PlayerRawStats  # noqa: E402


def phase_from_over(over_number: int) -> str:
    if over_number < 6:
        return "powerplay"
    if over_number < 15:
        return "middle"
    return "death"


@dataclass
class CounterSet:
    balls: int = 0
    runs: int = 0
    dismissals: int = 0
    wickets: int = 0
    dots: int = 0
    fours: int = 0
    sixes: int = 0


def safe_rate(numerator: float, denominator: float, multiplier: float = 1.0) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * multiplier


def minmax_1_99(series: pd.Series, invert: bool = False) -> pd.Series:
    min_v = float(series.min())
    max_v = float(series.max())
    if max_v - min_v < 1e-9:
        out = pd.Series([50.0] * len(series), index=series.index)
    else:
        out = 1 + 98 * ((series - min_v) / (max_v - min_v))
    if invert:
        out = 100 - out
    return out.clip(1, 99)


def load_player_styles(path: Path) -> Dict[str, Tuple[str, str]]:
    if not path.exists():
        return {}

    df = pd.read_csv(path)
    mapping: Dict[str, Tuple[str, str]] = {}
    for _, row in df.iterrows():
        mapping[str(row["player_name"]).strip()] = (
            str(row.get("bowling_style", "pace")).strip().lower(),
            str(row.get("arm", "right")).strip().lower(),
        )
    return mapping


def iter_cricsheet_matches(input_dir: Path):
    for zip_path in sorted(input_dir.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if member.endswith(".json"):
                    with zf.open(member) as handle:
                        try:
                            yield json.load(handle)
                        except json.JSONDecodeError:
                            continue


def extract_features(input_dir: Path, style_map: Dict[str, Tuple[str, str]]):
    batter_totals: Dict[str, CounterSet] = defaultdict(CounterSet)
    bowler_totals: Dict[str, CounterSet] = defaultdict(CounterSet)

    batter_phase: Dict[str, Dict[str, CounterSet]] = defaultdict(lambda: defaultdict(CounterSet))
    bowler_phase: Dict[str, Dict[str, CounterSet]] = defaultdict(lambda: defaultdict(CounterSet))

    batter_vs_type: Dict[Tuple[str, str], CounterSet] = defaultdict(CounterSet)
    batter_vs_arm: Dict[Tuple[str, str], CounterSet] = defaultdict(CounterSet)

    death_over_runs_conceded: Dict[str, list] = defaultdict(list)
    death_over_accum: Dict[Tuple[str, int, str], int] = defaultdict(int)

    matchup_table: Dict[Tuple[str, str], CounterSet] = defaultdict(CounterSet)

    for match in iter_cricsheet_matches(input_dir):
        innings_list = match.get("innings", [])
        match_id = (
            match.get("meta", {}).get("data_version", "v1")
            + "-"
            + str(match.get("info", {}).get("dates", ["unknown"])[0])
            + "-"
            + str(match.get("info", {}).get("event", {}).get("name", "event"))
        )

        for innings in innings_list:
            innings_obj = innings.get("overs") if isinstance(innings, dict) and "overs" in innings else None
            if innings_obj is None:
                for _, value in innings.items():
                    innings_obj = value.get("overs", [])
                    break
            overs = innings_obj or []

            for over_item in overs:
                over_no = int(over_item.get("over", 0))
                phase = phase_from_over(over_no)
                deliveries = over_item.get("deliveries", [])

                for delivery in deliveries:
                    batter = delivery.get("batter")
                    bowler = delivery.get("bowler")
                    if not batter or not bowler:
                        continue

                    runs_obj = delivery.get("runs", {})
                    batter_runs = int(runs_obj.get("batter", 0))
                    total_runs = int(runs_obj.get("total", batter_runs))
                    is_dot = total_runs == 0
                    is_four = batter_runs == 4
                    is_six = batter_runs == 6

                    wicket_events = delivery.get("wickets", []) or []
                    batter_out = any(w.get("player_out") == batter for w in wicket_events)
                    bowler_wicket = bool(wicket_events)

                    b_total = batter_totals[batter]
                    b_total.balls += 1
                    b_total.runs += batter_runs
                    b_total.dismissals += int(batter_out)
                    b_total.dots += int(is_dot)
                    b_total.fours += int(is_four)
                    b_total.sixes += int(is_six)

                    b_phase = batter_phase[batter][phase]
                    b_phase.balls += 1
                    b_phase.runs += batter_runs
                    b_phase.dismissals += int(batter_out)
                    b_phase.dots += int(is_dot)
                    b_phase.fours += int(is_four)
                    b_phase.sixes += int(is_six)

                    bo_total = bowler_totals[bowler]
                    bo_total.balls += 1
                    bo_total.runs += total_runs
                    bo_total.dismissals += int(bowler_wicket)
                    bo_total.wickets += int(bowler_wicket)
                    bo_total.dots += int(is_dot)

                    bo_phase = bowler_phase[bowler][phase]
                    bo_phase.balls += 1
                    bo_phase.runs += total_runs
                    bo_phase.dismissals += int(bowler_wicket)
                    bo_phase.wickets += int(bowler_wicket)
                    bo_phase.dots += int(is_dot)

                    bowl_style, bowl_arm = style_map.get(bowler, ("pace", "right"))

                    b_vs_type = batter_vs_type[(batter, bowl_style)]
                    b_vs_type.balls += 1
                    b_vs_type.runs += batter_runs
                    b_vs_type.dismissals += int(batter_out)

                    b_vs_arm = batter_vs_arm[(batter, bowl_arm)]
                    b_vs_arm.balls += 1
                    b_vs_arm.runs += batter_runs
                    b_vs_arm.dismissals += int(batter_out)

                    mu = matchup_table[(batter, bowler)]
                    mu.balls += 1
                    mu.runs += batter_runs
                    mu.dismissals += int(batter_out)

                    if phase == "death":
                        death_over_accum[(match_id, over_no, bowler)] += total_runs

    for (_, _, bowler), runs in death_over_accum.items():
        death_over_runs_conceded[bowler].append(runs)

    records = []
    players = sorted(set(list(batter_totals.keys()) + list(bowler_totals.keys())))

    for player in players:
        bt = batter_totals[player]
        bw = bowler_totals[player]

        pp = batter_phase[player]["powerplay"]
        mid = batter_phase[player]["middle"]
        death = batter_phase[player]["death"]

        bpp = bowler_phase[player]["powerplay"]
        bmid = bowler_phase[player]["middle"]
        bdeath = bowler_phase[player]["death"]

        pace = batter_vs_type[(player, "pace")]
        spin = batter_vs_type[(player, "spin")]
        left = batter_vs_arm[(player, "left")]
        right = batter_vs_arm[(player, "right")]

        rotate_balls = max(0, bt.balls - bt.fours - bt.sixes)

        records.append(
            {
                "player_name": player,
                "balls_faced": bt.balls,
                "runs_scored": bt.runs,
                "dismissals": bt.dismissals,
                "balls_bowled": bw.balls,
                "runs_conceded": bw.runs,
                "wickets_taken": bw.wickets,
                "overall_sr": safe_rate(bt.runs, bt.balls, 100),
                "sr_powerplay": safe_rate(pp.runs, pp.balls, 100),
                "sr_middle": safe_rate(mid.runs, mid.balls, 100),
                "sr_death": safe_rate(death.runs, death.balls, 100),
                "boundary_pct": safe_rate(bt.fours + bt.sixes, bt.balls, 100),
                "dot_pct_faced": safe_rate(bt.dots, bt.balls, 100),
                "dismissal_rate_powerplay": safe_rate(pp.dismissals, pp.balls, 100),
                "dismissal_rate_middle": safe_rate(mid.dismissals, mid.balls, 100),
                "dismissal_rate_death": safe_rate(death.dismissals, death.balls, 100),
                "dot_pct_delivered": safe_rate(bw.dots, bw.balls, 100),
                "economy_powerplay": safe_rate(bpp.runs, bpp.balls, 6),
                "economy_middle": safe_rate(bmid.runs, bmid.balls, 6),
                "economy_death": safe_rate(bdeath.runs, bdeath.balls, 6),
                "wicket_rate_powerplay": safe_rate(bpp.wickets, bpp.balls, 100),
                "wicket_rate_middle": safe_rate(bmid.wickets, bmid.balls, 100),
                "wicket_rate_death": safe_rate(bdeath.wickets, bdeath.balls, 100),
                "death_runs_per_over": float(np.mean(death_over_runs_conceded[player]))
                if death_over_runs_conceded[player]
                else 0.0,
                "sr_vs_pace": safe_rate(pace.runs, pace.balls, 100),
                "dismissal_rate_vs_pace": safe_rate(pace.dismissals, pace.balls, 100),
                "sr_vs_spin": safe_rate(spin.runs, spin.balls, 100),
                "dismissal_rate_vs_spin": safe_rate(spin.dismissals, spin.balls, 100),
                "sr_vs_left_arm": safe_rate(left.runs, left.balls, 100),
                "dismissal_rate_vs_left_arm": safe_rate(left.dismissals, left.balls, 100),
                "sr_vs_right_arm": safe_rate(right.runs, right.balls, 100),
                "dismissal_rate_vs_right_arm": safe_rate(right.dismissals, right.balls, 100),
                "rotation_pct": safe_rate(rotate_balls, bt.balls, 100),
            }
        )

    raw_df = pd.DataFrame(records)
    matchup_records = [
        {
            "batter_name": batter,
            "bowler_name": bowler,
            "balls": c.balls,
            "runs": c.runs,
            "dismissals": c.dismissals,
        }
        for (batter, bowler), c in matchup_table.items()
        if c.balls >= 12
    ]
    matchup_df = pd.DataFrame(matchup_records)

    return raw_df, matchup_df


def derive_ratings(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame()

    # Batting signals
    df["power_metric"] = 0.6 * df["boundary_pct"] + 0.4 * df["sr_death"]
    df["timing_metric"] = 0.6 * df["overall_sr"] + 0.4 * (100 - df["dot_pct_faced"])
    df["pace_handling_metric"] = df["sr_vs_pace"] - (1.8 * df["dismissal_rate_vs_pace"])
    df["spin_handling_metric"] = df["sr_vs_spin"] - (1.8 * df["dismissal_rate_vs_spin"])
    df["strike_rotation_metric"] = 0.7 * df["rotation_pct"] + 0.3 * (100 - df["dot_pct_faced"])
    df["aggression_metric"] = 0.55 * df["boundary_pct"] + 0.45 * df["sr_powerplay"]
    df["temperament_metric"] = 100 - (0.5 * df["dismissal_rate_middle"] + 0.5 * df["dismissal_rate_death"])
    df["clutch_metric"] = 0.6 * df["sr_death"] + 0.4 * (100 - df["dismissal_rate_death"])
    df["death_performance_metric"] = 0.7 * df["sr_death"] + 0.3 * df["boundary_pct"]

    # Bowling signals
    df["pace_metric"] = 0.7 * df["wicket_rate_powerplay"] + 0.3 * (100 - df["economy_powerplay"] * 7)
    df["swing_metric"] = 0.6 * df["wicket_rate_powerplay"] + 0.4 * (100 - df["economy_powerplay"] * 8)
    df["seam_metric"] = 0.6 * df["dot_pct_delivered"] + 0.4 * df["wicket_rate_middle"]
    df["spin_metric"] = 0.6 * df["wicket_rate_middle"] + 0.4 * (100 - df["economy_middle"] * 8)
    df["yorkers_metric"] = 0.7 * df["wicket_rate_death"] + 0.3 * (100 - df["economy_death"] * 7)
    df["variations_metric"] = 0.6 * df["wicket_rate_death"] + 0.4 * df["dot_pct_delivered"]
    df["control_metric"] = 100 - (df["economy_middle"] * 10)
    df["death_bowling_metric"] = 0.5 * df["wicket_rate_death"] + 0.5 * (100 - df["death_runs_per_over"] * 8)
    df["pressure_handling_metric"] = 0.6 * df["wicket_rate_death"] + 0.4 * (100 - df["economy_death"] * 9)

    metric_cols = [
        "power_metric",
        "timing_metric",
        "pace_handling_metric",
        "spin_handling_metric",
        "strike_rotation_metric",
        "aggression_metric",
        "temperament_metric",
        "clutch_metric",
        "death_performance_metric",
        "pace_metric",
        "swing_metric",
        "seam_metric",
        "spin_metric",
        "yorkers_metric",
        "variations_metric",
        "control_metric",
        "death_bowling_metric",
        "pressure_handling_metric",
    ]

    for col in metric_cols:
        df[col] = df[col].fillna(0.0)

    rating_map = {
        "power": "power_metric",
        "timing": "timing_metric",
        "pace_handling": "pace_handling_metric",
        "spin_handling": "spin_handling_metric",
        "strike_rotation": "strike_rotation_metric",
        "aggression": "aggression_metric",
        "temperament": "temperament_metric",
        "clutch": "clutch_metric",
        "death_performance": "death_performance_metric",
        "pace": "pace_metric",
        "swing": "swing_metric",
        "seam": "seam_metric",
        "spin": "spin_metric",
        "yorkers": "yorkers_metric",
        "variations": "variations_metric",
        "control": "control_metric",
        "death_bowling": "death_bowling_metric",
        "pressure_handling": "pressure_handling_metric",
    }

    for rating, metric in rating_map.items():
        df[rating] = minmax_1_99(df[metric]).round().astype(int)

    low_sample = (df["balls_faced"] < 50) & (df["balls_bowled"] < 60)
    fallback_cols = list(rating_map.keys())
    for col in fallback_cols:
        df.loc[low_sample, col] = 55

    keep_cols = ["player_name", *fallback_cols]
    return df[keep_cols]


def upsert_database(raw_df: pd.DataFrame, rating_df: pd.DataFrame, matchup_df: pd.DataFrame):
    session = SessionLocal()
    try:
        players_by_name: Dict[str, Player] = {}

        for player_name in raw_df["player_name"].unique():
            existing = session.execute(select(Player).where(Player.name == player_name)).scalar_one_or_none()
            if existing is None:
                existing = Player(name=player_name, external_key=player_name.lower().replace(" ", "_"))
                session.add(existing)
                session.flush()
            players_by_name[player_name] = existing

        session.execute(delete(PlayerRawStats))
        session.execute(delete(PlayerRating))
        session.execute(delete(BatterBowlerMatchup))

        for _, row in raw_df.iterrows():
            p = players_by_name[row["player_name"]]
            stats_json = {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v) for k, v in row.items() if k != "player_name"}
            session.add(
                PlayerRawStats(
                    player_id=p.id,
                    season="all",
                    balls_faced=int(row["balls_faced"]),
                    runs_scored=int(row["runs_scored"]),
                    dismissals=int(row["dismissals"]),
                    balls_bowled=int(row["balls_bowled"]),
                    runs_conceded=int(row["runs_conceded"]),
                    wickets_taken=int(row["wickets_taken"]),
                    stats_json=stats_json,
                )
            )

        for _, row in rating_df.iterrows():
            p = players_by_name[row["player_name"]]
            data = row.to_dict()
            data.pop("player_name", None)
            session.add(PlayerRating(player_id=p.id, version="latest", raw_snapshot=data, **data))

        for _, row in matchup_df.iterrows():
            batter = players_by_name.get(row["batter_name"])
            bowler = players_by_name.get(row["bowler_name"])
            if not batter or not bowler:
                continue
            session.add(
                BatterBowlerMatchup(
                    batter_id=batter.id,
                    bowler_id=bowler.id,
                    balls=int(row["balls"]),
                    runs=int(row["runs"]),
                    dismissals=int(row["dismissals"]),
                )
            )

        session.commit()
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="CricketOS Cricsheet ETL pipeline")
    parser.add_argument("--input-dir", default=str(PROJECT_ROOT / "data" / "input"), help="Directory with Cricsheet zip files")
    parser.add_argument("--styles-csv", default=str(PROJECT_ROOT / "data" / "input" / "player_styles.csv"))
    parser.add_argument("--raw-output", default=str(PROJECT_ROOT / "data" / "processed" / "player_raw_stats.csv"))
    parser.add_argument("--rating-output", default=str(PROJECT_ROOT / "data" / "processed" / "player_ratings.csv"))
    parser.add_argument("--matchup-output", default=str(PROJECT_ROOT / "data" / "processed" / "matchups.csv"))
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    style_map = load_player_styles(Path(args.styles_csv))

    raw_df, matchup_df = extract_features(input_dir, style_map)
    rating_df = derive_ratings(raw_df)

    raw_df.to_csv(args.raw_output, index=False)
    rating_df.to_csv(args.rating_output, index=False)
    matchup_df.to_csv(args.matchup_output, index=False)

    upsert_database(raw_df, rating_df, matchup_df)

    print(f"Raw stats rows: {len(raw_df)}")
    print(f"Rating rows: {len(rating_df)}")
    print(f"Matchup rows (12+ balls): {len(matchup_df)}")


if __name__ == "__main__":
    main()
