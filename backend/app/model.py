"""Pure baseball math shared by the ingest script and the API.

Everything here is deterministic and dependency-free so it can be unit tested
and so the API never has to ask a language model for a number.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from statistics import NormalDist

_NORMAL = NormalDist()

HITTER_RATINGS = ("contact", "power", "eye", "speed", "glove", "arm")
PITCHER_RATINGS = ("stuff", "contact_mgmt", "control", "velocity", "stamina")

RATING_LABELS = {
    "contact": "Contact",
    "power": "Power",
    "eye": "Eye",
    "speed": "Speed",
    "glove": "Glove",
    "arm": "Arm",
    "stuff": "Stuff",
    "contact_mgmt": "Weak contact",
    "control": "Control",
    "velocity": "Velocity",
    "stamina": "Stamina",
}

# Which Savant percentile columns feed each rating. Savant already orients
# percentiles so that higher is better (e.g. a high k_percent percentile for a
# hitter means he strikes out rarely).
HITTER_INPUTS = {
    "contact": ("k_percent", "whiff_percent", "xba", "squared_up_rate"),
    "power": ("xslg", "brl_percent", "max_ev", "hard_hit_percent", "bat_speed"),
    "eye": ("bb_percent", "chase_percent"),
    "speed": ("sprint_speed",),
    "glove": ("oaa",),
    "arm": ("arm_strength",),
}
PITCHER_INPUTS = {
    "stuff": ("whiff_percent", "k_percent", "chase_percent"),
    "contact_mgmt": ("brl_percent", "hard_hit_percent", "exit_velocity", "xslg"),
    "control": ("bb_percent",),
    "velocity": ("fb_velocity",),
}

# Positional adjustment in runs per 650 PA (FanGraphs-style convention).
POSITION_ADJ = {
    "C": 12.5,
    "SS": 7.5,
    "2B": 2.5,
    "3B": 2.5,
    "CF": 2.5,
    "LF": -7.5,
    "RF": -7.5,
    "1B": -12.5,
    "DH": -17.5,
    "OF": -2.5,
    "IF": 2.5,
}

RUNS_PER_WIN = 10.0


def percentile_to_scout(pct: float | None) -> int | None:
    """Map a 0-100 percentile to the 20-80 scouting scale (50 = average, 10 = 1 SD)."""
    if pct is None:
        return None
    p = min(max(float(pct), 0.5), 99.5) / 100.0
    return int(round(min(80, max(20, 50 + 10 * _NORMAL.inv_cdf(p)))))


def mean_present(values: Iterable[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def ratings_from_percentiles(pcts: dict, inputs: dict) -> dict:
    return {k: percentile_to_scout(mean_present(pcts.get(c) for c in cols)) for k, cols in inputs.items()}


def stamina_rating(innings: float, games: int, games_started: int) -> int | None:
    if not games:
        return None
    ip_per_g = innings / games
    # ~1 IP/G (reliever) -> 30, ~6 IP/G (starter) -> 70
    return int(round(min(80, max(20, 22 + 8 * ip_per_g))))


def hitter_war(woba: float, lg_woba: float, pa: int, position: str, glove: int | None) -> float:
    batting = (woba - lg_woba) / 1.2 * pa
    replacement = 20.0 * pa / 600
    positional = POSITION_ADJ.get(position, 0.0) * pa / 650
    fielding = ((glove - 50) / 10 * 4.0 * pa / 650) if glove is not None else 0.0
    return round((batting + replacement + positional + fielding) / RUNS_PER_WIN, 1)


def fip(hr: int, bb: int, hbp: int, k: int, ip: float, constant: float) -> float | None:
    if ip <= 0:
        return None
    return (13 * hr + 3 * (bb + hbp) - 2 * k) / ip + constant


def pitcher_war(fip_value: float | None, lg_fip: float, ip: float, starter: bool) -> float:
    if fip_value is None or ip <= 0:
        return 0.0
    replacement_gap = 1.0 if starter else 0.6
    runs = ((lg_fip + replacement_gap) - fip_value) / 9 * ip
    return round(runs / RUNS_PER_WIN, 1)


def innings_to_float(ip: str | float | None) -> float:
    """Convert MLB '123.2' (2 outs) notation to true innings."""
    if ip in (None, ""):
        return 0.0
    whole, _, outs = str(ip).partition(".")
    return int(whole or 0) + (int(outs or 0) / 3)


def age_delta(age: int, pitcher: bool) -> float:
    """Simple yearly WAR change by age; intentionally conservative."""
    if age <= 25:
        return 0.3
    if age <= 29:
        return 0.0
    if age <= 32:
        return -0.3 if not pitcher else -0.35
    return -0.5


def project_war(war: float, age: int, years: int, pitcher: bool, sample_weight: float) -> list[float]:
    """Regress last season toward a modest baseline, then age it forward."""
    # Unknown players regress toward a fringe-roster baseline, not an average regular.
    baseline = 0.5 if not pitcher else 0.3
    base = sample_weight * war + (1 - sample_weight) * baseline
    out, cur = [], base
    for i in range(years):
        cur = cur + age_delta(age + i, pitcher)
        out.append(round(max(cur, -1.0), 1))
    return out


def surplus_value(
    projected_war: list[float], salaries: list[float], dollars_per_war: float, inflation: float = 0.03
) -> float:
    total = 0.0
    for i, (w, s) in enumerate(zip(projected_war, salaries, strict=False)):
        total += w * dollars_per_war * ((1 + inflation) ** i) - s
    return round(total, 1)


def scale_rating(value: float | None, lo: float, hi: float) -> int | None:
    if value is None:
        return None
    t = (value - lo) / (hi - lo)
    return int(round(min(80, max(20, 20 + 60 * t))))


ARCHETYPES = [
    # id, label, group, description, rule(ratings, extras) -> bool, profile
    (
        "three-true-outcomes",
        "Three true outcomes",
        "hitter",
        "Big power and walks, swing-and-miss accepted.",
        lambda r, e: _ge(r, "power", 60) and _ge(r, "eye", 55) and _le(r, "contact", 45),
        {"power": 70, "eye": 60, "contact": 35},
    ),
    ("slugger", "Slugger", "hitter", "Top-tier impact on contact.", lambda r, e: _ge(r, "power", 63), {"power": 70}),
    (
        "contact-artist",
        "Contact artist",
        "hitter",
        "Puts the ball in play, rarely whiffs.",
        lambda r, e: _ge(r, "contact", 62) and _le(r, "power", 50),
        {"contact": 70, "power": 40},
    ),
    (
        "table-setter",
        "Table setter",
        "hitter",
        "Gets on base and runs.",
        lambda r, e: _ge(r, "eye", 57) and _ge(r, "contact", 52) and _ge(r, "speed", 55),
        {"eye": 62, "contact": 58, "speed": 60},
    ),
    ("burner", "Burner", "hitter", "Elite sprint speed.", lambda r, e: _ge(r, "speed", 65), {"speed": 72}),
    (
        "glove-first",
        "Glove-first",
        "hitter",
        "Defense carries the profile.",
        lambda r, e: _ge(r, "glove", 62) and _le(r, "power", 47),
        {"glove": 70, "power": 40},
    ),
    (
        "cannon",
        "Cannon arm",
        "hitter",
        "Throwing arm that changes the running game.",
        lambda r, e: _ge(r, "arm", 65),
        {"arm": 72},
    ),
    (
        "five-tool",
        "Five-tool",
        "hitter",
        "Above average across every tool.",
        lambda r, e: all(_ge(r, k, 53) for k in ("contact", "power", "speed", "glove", "arm")),
        {"contact": 58, "power": 58, "speed": 58, "glove": 58, "arm": 58},
    ),
    (
        "patient-eye",
        "Patient eye",
        "hitter",
        "Elite walk rate and chase discipline.",
        lambda r, e: _ge(r, "eye", 65),
        {"eye": 72},
    ),
    (
        "strikeout-artist",
        "Strikeout artist",
        "pitcher",
        "Misses bats at an elite rate.",
        lambda r, e: _ge(r, "stuff", 64),
        {"stuff": 72},
    ),
    (
        "flamethrower",
        "Flamethrower",
        "pitcher",
        "Top-of-the-scale fastball velocity.",
        lambda r, e: _ge(r, "velocity", 68),
        {"velocity": 74},
    ),
    (
        "command",
        "Command pitcher",
        "pitcher",
        "Lives in the zone, limits walks.",
        lambda r, e: _ge(r, "control", 64),
        {"control": 72},
    ),
    (
        "weak-contact",
        "Weak contact",
        "pitcher",
        "Suppresses barrels and hard hits.",
        lambda r, e: _ge(r, "contact_mgmt", 64),
        {"contact_mgmt": 70},
    ),
    (
        "workhorse",
        "Workhorse",
        "pitcher",
        "Eats innings as a starter.",
        lambda r, e: e.get("role") == "SP" and _ge(r, "stamina", 66),
        {"stamina": 72},
    ),
    (
        "high-leverage",
        "High-leverage arm",
        "pitcher",
        "Bullpen weapon with bat-missing stuff.",
        lambda r, e: e.get("role") == "RP" and _ge(r, "stuff", 60) and _ge(r, "velocity", 55),
        {"stuff": 66, "velocity": 62, "stamina": 30},
    ),
]


def _ge(r: dict, k: str, v: int) -> bool:
    return r.get(k) is not None and r[k] >= v


def _le(r: dict, k: str, v: int) -> bool:
    return r.get(k) is not None and r[k] <= v


def archetypes_for(ratings: dict, group: str, extras: dict) -> list[str]:
    return [a[0] for a in ARCHETYPES if a[2] == group and a[4](ratings, extras)]


def rating_distance(a: dict, b: dict, keys: Iterable[str]) -> float | None:
    shared = [k for k in keys if a.get(k) is not None and b.get(k) is not None]
    if len(shared) < 3:
        return None
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in shared) / len(shared))
