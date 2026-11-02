"""In-memory player store loaded from players.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .config import get_settings


class Store:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.meta: dict = data["meta"]
        self.teams: list[dict] = data["teams"]
        self.players: list[dict] = data["players"]
        self.by_id: dict[int, dict] = {p["id"]: p for p in self.players}
        self.team_by_abbrev: dict[str, dict] = {t["abbrev"].upper(): t for t in self.teams}
        self.team_by_id: dict[int, dict] = {t["id"]: t for t in self.teams}

    def team(self, key: str | int) -> dict | None:
        if isinstance(key, int) or str(key).isdigit():
            return self.team_by_id.get(int(key))
        k = str(key).strip().upper()
        if k in self.team_by_abbrev:
            return self.team_by_abbrev[k]
        low = str(key).strip().lower()
        for t in self.teams:
            if low in (t["name"].lower(), t["short"].lower()):
                return t
        return None

    def roster(self, team_id: int) -> list[dict]:
        return [p for p in self.players if p["team_id"] == team_id]

    def find_by_name(self, name: str) -> dict | None:
        low = name.strip().lower()
        exact = [p for p in self.players if p["name"].lower() == low]
        if exact:
            return exact[0]
        partial = [p for p in self.players if low and low in p["name"].lower()]
        return partial[0] if len(partial) == 1 else None


@lru_cache(maxsize=1)
def get_store() -> Store:
    return Store(get_settings().players_file)
