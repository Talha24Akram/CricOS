from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    short_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)

    players = relationship("TeamPlayer", back_populates="team", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    batting_style: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bowling_style: Mapped[str | None] = mapped_column(String(40), nullable=True)
    arm: Mapped[str | None] = mapped_column(String(10), nullable=True)

    team_links = relationship("TeamPlayer", back_populates="player", cascade="all, delete-orphan")
    raw_stats = relationship("PlayerRawStats", back_populates="player", cascade="all, delete-orphan")
    ratings = relationship("PlayerRating", back_populates="player", cascade="all, delete-orphan")


class TeamPlayer(Base):
    __tablename__ = "team_players"
    __table_args__ = (UniqueConstraint("team_id", "player_id", name="uq_team_player"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    team = relationship("Team", back_populates="players")
    player = relationship("Player", back_populates="team_links")


class PlayerRawStats(Base):
    __tablename__ = "player_raw_stats"
    __table_args__ = (UniqueConstraint("player_id", "season", name="uq_raw_player_season"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    season: Mapped[str] = mapped_column(String(20), default="all")

    balls_faced: Mapped[int] = mapped_column(Integer, default=0)
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)
    dismissals: Mapped[int] = mapped_column(Integer, default=0)
    balls_bowled: Mapped[int] = mapped_column(Integer, default=0)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    wickets_taken: Mapped[int] = mapped_column(Integer, default=0)

    stats_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player = relationship("Player", back_populates="raw_stats")


class PlayerRating(Base):
    __tablename__ = "player_ratings"
    __table_args__ = (UniqueConstraint("player_id", "version", name="uq_rating_player_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(40), default="latest")

    power: Mapped[int] = mapped_column(Integer, default=50)
    timing: Mapped[int] = mapped_column(Integer, default=50)
    pace_handling: Mapped[int] = mapped_column(Integer, default=50)
    spin_handling: Mapped[int] = mapped_column(Integer, default=50)
    strike_rotation: Mapped[int] = mapped_column(Integer, default=50)
    aggression: Mapped[int] = mapped_column(Integer, default=50)
    temperament: Mapped[int] = mapped_column(Integer, default=50)
    clutch: Mapped[int] = mapped_column(Integer, default=50)
    death_performance: Mapped[int] = mapped_column(Integer, default=50)

    pace: Mapped[int] = mapped_column(Integer, default=50)
    swing: Mapped[int] = mapped_column(Integer, default=50)
    seam: Mapped[int] = mapped_column(Integer, default=50)
    spin: Mapped[int] = mapped_column(Integer, default=50)
    yorkers: Mapped[int] = mapped_column(Integer, default=50)
    variations: Mapped[int] = mapped_column(Integer, default=50)
    control: Mapped[int] = mapped_column(Integer, default=50)
    death_bowling: Mapped[int] = mapped_column(Integer, default=50)
    pressure_handling: Mapped[int] = mapped_column(Integer, default=50)

    raw_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)

    player = relationship("Player", back_populates="ratings")


class BatterBowlerMatchup(Base):
    __tablename__ = "batter_bowler_matchups"
    __table_args__ = (UniqueConstraint("batter_id", "bowler_id", name="uq_batter_bowler"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    bowler_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    balls: Mapped[int] = mapped_column(Integer, default=0)
    runs: Mapped[int] = mapped_column(Integer, default=0)
    dismissals: Mapped[int] = mapped_column(Integer, default=0)


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    city: Mapped[str] = mapped_column(String(80), default="")
    boundary_size: Mapped[str] = mapped_column(String(12), default="medium")
    six_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    pace_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    spin_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
