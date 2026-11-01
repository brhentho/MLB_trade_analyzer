"""Runtime configuration, read from the environment on each call. Money is in millions of USD."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


@dataclass(frozen=True)
class Settings:
    stats_season: int = 2026
    plan_season: int = 2027
    league_min: float = 0.78
    cbt_threshold: float = 244.0
    dollars_per_war: float = 9.0
    openai_model: str = "gpt-4o"
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    rate_limit_per_minute: int = 10
    players_file: Path = DATA_DIR / "players.json"

    @property
    def openai_configured(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))


def get_settings() -> Settings:
    env = os.getenv
    return Settings(
        stats_season=int(env("STATS_SEASON", "2026")),
        plan_season=int(env("PLAN_SEASON", "2027")),
        league_min=float(env("LEAGUE_MIN_M", "0.78")),
        cbt_threshold=float(env("CBT_THRESHOLD_M", "244")),
        dollars_per_war=float(env("DOLLARS_PER_WAR_M", "9.0")),
        openai_model=env("OPENAI_MODEL", "gpt-4o"),
        allowed_origins=tuple(
            o.strip() for o in env("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()
        ),
        rate_limit_per_minute=int(env("AI_RATE_LIMIT_PER_MINUTE", "10")),
        players_file=Path(env("PLAYERS_FILE", str(DATA_DIR / "players.json"))),
    )
