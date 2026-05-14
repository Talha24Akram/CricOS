from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.models.tables import Player, PlayerRating, PlayerRawStats  # noqa: E402


def main() -> None:
    session = SessionLocal()
    try:
        rows = session.execute(
            select(Player.name, PlayerRawStats.stats_json, PlayerRating)
            .join(PlayerRawStats, PlayerRawStats.player_id == Player.id)
            .join(PlayerRating, PlayerRating.player_id == Player.id)
            .limit(5)
        ).all()

        if not rows:
            print("No data found. Run data/pipeline.py first.")
            return

        for idx, (name, raw_stats, rating) in enumerate(rows, start=1):
            print(f"\n[{idx}] {name}")
            print(
                f"  Raw: SR={raw_stats.get('overall_sr', 0):.2f}, "
                f"Boundary%={raw_stats.get('boundary_pct', 0):.2f}, "
                f"WktRateDeath={raw_stats.get('wicket_rate_death', 0):.2f}, "
                f"EcoDeath={raw_stats.get('economy_death', 0):.2f}"
            )
            print(
                f"  Ratings: power={rating.power}, timing={rating.timing}, death={rating.death_performance}, "
                f"pace={rating.pace}, spin={rating.spin}, death_bowling={rating.death_bowling}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
