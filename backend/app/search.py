"""Player search: structured filters, explanations, similarity and a rule-based query parser."""

from __future__ import annotations

import re

from . import model
from .schemas import SearchFilters

OF = {"LF", "CF", "RF"}
IF = {"1B", "2B", "3B", "SS"}

PERCENTILE_LABELS = {
    "xwoba": "xwOBA",
    "xba": "xBA",
    "xslg": "xSLG",
    "xiso": "xISO",
    "xobp": "xOBP",
    "brl_percent": "Barrel%",
    "exit_velocity": "Avg EV",
    "max_ev": "Max EV",
    "hard_hit_percent": "Hard-Hit%",
    "k_percent": "K%",
    "bb_percent": "BB%",
    "whiff_percent": "Whiff%",
    "chase_percent": "Chase%",
    "arm_strength": "Arm Strength",
    "sprint_speed": "Sprint Speed",
    "oaa": "OAA",
    "bat_speed": "Bat Speed",
    "squared_up_rate": "Squared-Up%",
    "xera": "xERA",
    "fb_velocity": "FB Velo",
    "fb_spin": "FB Spin",
    "curve_spin": "CB Spin",
}


def control_years(p: dict, plan_season: int) -> int:
    return max(0, p["contract"]["control_through"] - plan_season + 1)


def _pos_match(p: dict, positions: list[str]) -> bool:
    wanted = {x.upper() for x in positions}
    pos = p["position"]
    if p["group"] == "pitcher":
        return bool(wanted & {"P", p["role"]})
    return pos in wanted or ("OF" in wanted and pos in OF) or ("IF" in wanted and pos in IF)


def _ordinal(n: float) -> str:
    n = int(round(n))
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def evaluate(p: dict, f: SearchFilters, plan_season: int) -> list[dict] | None:
    """Return match reasons if the player passes every filter, else None."""
    reasons: list[dict] = []
    if f.group and p["group"] != f.group:
        return None
    if f.positions:
        if not _pos_match(p, f.positions):
            return None
        reasons.append({"label": p["role"] if p["group"] == "pitcher" else p["position"], "kind": "position"})
    if f.roles:
        if p["group"] != "pitcher" or p["role"] not in f.roles:
            return None
        if not f.positions:
            reasons.append({"label": p["role"], "kind": "position"})
    if f.bats and p.get("bats") not in f.bats:
        return None
    if f.throws:
        if p.get("throws") not in f.throws:
            return None
        reasons.append({"label": f"Throws {p['throws']}", "kind": "bio"})
    if f.bats:
        reasons.append({"label": f"Bats {p['bats']}", "kind": "bio"})
    if f.teams and p["team"].upper() not in {t.upper() for t in f.teams}:
        return None
    if f.age_min is not None and p["age"] < f.age_min:
        return None
    if f.age_max is not None and p["age"] > f.age_max:
        return None
    if f.age_min is not None or f.age_max is not None:
        reasons.append({"label": f"Age {p['age']}", "kind": "bio"})
    if f.archetypes:
        if not set(f.archetypes) <= set(p["archetypes"]):
            return None
        for a in f.archetypes:
            reasons.append({"label": ARCHETYPE_LABELS.get(a, a), "kind": "archetype"})
    for key, floor in (f.ratings_min or {}).items():
        val = p["ratings"].get(key)
        if val is None or val < floor:
            return None
        reasons.append({"label": f"{model.RATING_LABELS.get(key, key)} {val}", "kind": "rating", "value": val})
    for key, ceil in (f.ratings_max or {}).items():
        val = p["ratings"].get(key)
        if val is None or val > ceil:
            return None
        reasons.append({"label": f"{model.RATING_LABELS.get(key, key)} {val}", "kind": "rating", "value": val})
    for key, floor in (f.percentiles_min or {}).items():
        val = p.get("percentiles", {}).get(key)
        if val is None or val < floor:
            return None
        reasons.append(
            {"label": f"{PERCENTILE_LABELS.get(key, key)} {_ordinal(val)} pct", "kind": "percentile", "value": val}
        )
    if f.salary_max is not None:
        sal = p["contract"]["salary_now"]
        if sal > f.salary_max:
            return None
        reasons.append({"label": f"${sal:.1f}M in {plan_season}", "kind": "money", "value": sal})
    if f.control_min_years is not None:
        yrs = control_years(p, plan_season)
        if yrs < f.control_min_years:
            return None
        reasons.append({"label": f"{yrs} yr{'s' if yrs != 1 else ''} control", "kind": "money", "value": yrs})
    if f.war_min is not None:
        if p["war"] < f.war_min:
            return None
        reasons.append({"label": f"{p['war']:.1f} sWAR", "kind": "value", "value": p["war"]})
    if f.verified_only and not p["contract"]["verified"]:
        return None
    return reasons


def sort_value(p: dict, key: str) -> float:
    if key.startswith("rating:"):
        return p["ratings"].get(key.split(":", 1)[1]) or 0
    if key.startswith("pct:"):
        return p.get("percentiles", {}).get(key.split(":", 1)[1]) or 0
    if key == "salary":
        return p["contract"]["salary_now"]
    if key == "value":
        return p["war"] / max(p["contract"]["salary_now"], 0.78)
    return p.get(key) or 0


def search(players: list[dict], f: SearchFilters, plan_season: int) -> dict:
    hits = []
    for p in players:
        reasons = evaluate(p, f, plan_season)
        if reasons is not None:
            hits.append((p, reasons))
    hits.sort(key=lambda h: sort_value(h[0], f.sort), reverse=f.descending)
    page = hits[f.offset : f.offset + f.limit]
    return {"total": len(hits), "results": [{"player": p, "reasons": r} for p, r in page]}


def similar(
    target: dict,
    players: list[dict],
    limit: int,
    plan_season: int,
    salary_max: float | None = None,
    control_min_years: int | None = None,
) -> list[dict]:
    keys = model.HITTER_RATINGS if target["group"] == "hitter" else model.PITCHER_RATINGS
    out = []
    for p in players:
        if p["id"] == target["id"] or p["group"] != target["group"]:
            continue
        if target["group"] == "pitcher" and p["role"] != target["role"]:
            continue
        if salary_max is not None and p["contract"]["salary_now"] > salary_max:
            continue
        if control_min_years is not None and control_years(p, plan_season) < control_min_years:
            continue
        d = model.rating_distance(target["ratings"], p["ratings"], keys)
        if d is None:
            continue
        out.append((d, p))
    out.sort(key=lambda x: x[0])
    results = []
    for d, p in out[:limit]:
        results.append(
            {
                "player": p,
                "similarity": round(max(0.0, 100 - d * 4), 1),
                "salary_delta": round(p["contract"]["salary_now"] - target["contract"]["salary_now"], 2),
                "control_delta": control_years(p, plan_season) - control_years(target, plan_season),
                "age_delta": p["age"] - target["age"],
            }
        )
    return results


def nearest_to_profile(profile: dict[str, int], players: list[dict], group: str, limit: int) -> list[dict]:
    """'Draw the shape' search: nearest players to an arbitrary rating profile."""
    keys = [k for k, v in profile.items() if v is not None]
    if not keys:
        return []
    scored = []
    for p in players:
        if p["group"] != group or any(p["ratings"].get(k) is None for k in keys):
            continue
        d = (sum((profile[k] - p["ratings"][k]) ** 2 for k in keys) / len(keys)) ** 0.5
        scored.append((d, p))
    scored.sort(key=lambda x: x[0])
    return [{"player": p, "similarity": round(max(0.0, 100 - d * 4), 1)} for d, p in scored[:limit]]


ARCHETYPE_LABELS = {a[0]: a[1] for a in model.ARCHETYPES}

_POSITION_WORDS = {
    r"\bcatchers?\b": "C",
    r"\bfirst base(man)?\b|\b1b\b": "1B",
    r"\bsecond base(man)?\b|\b2b\b": "2B",
    r"\bthird base(man)?\b|\b3b\b": "3B",
    r"\bshortstops?\b|\bss\b": "SS",
    r"\bcenter field(er)?\b|\bcf\b": "CF",
    r"\bleft field(er)?\b|\blf\b": "LF",
    r"\bright field(er)?\b|\brf\b": "RF",
    r"\boutfield(ers?)?\b|\bof\b": "OF",
    r"\binfield(ers?)?\b": "IF",
    r"\bdh\b|\bdesignated hitter\b": "DH",
}
_RATING_WORDS = {
    r"\bpower\b|\bslug": ("power", 60),
    r"\bcontact\b": ("contact", 60),
    r"\bspeed\b|\bfast\b|\bburner\b": ("speed", 62),
    r"\bdefen[cs]e\b|\bglove\b|\bdefensive\b": ("glove", 60),
    r"\barm\b": ("arm", 62),
    r"\bdiscipline\b|\bpatient\b|\bwalks?\b|\beye\b": ("eye", 60),
    r"\bstrikeouts?\b|\bswing.and.miss\b|\bwhiffs?\b|\bstuff\b": ("stuff", 60),
    r"\bvelo(city)?\b|\bhard.thrower\b|\bthrows? hard\b": ("velocity", 62),
    r"\bcommand\b|\bcontrol\b": ("control", 60),
    r"\bweak contact\b|\bground.?ball": ("contact_mgmt", 60),
    r"\binnings eater\b|\bdurable\b": ("stamina", 62),
}
_PERCENTILE_WORDS = {
    r"\bchase\b": "chase_percent",
    r"\bbarrels?\b": "brl_percent",
    r"\bexit velo": "exit_velocity",
    r"\bspin\b": "fb_spin",
    r"\bsprint\b": "sprint_speed",
    r"\bbat speed\b": "bat_speed",
}


def parse_query(text: str) -> tuple[SearchFilters, list[str]]:
    """Deterministic natural-language → filter parser. Used when no LLM is configured."""
    q = text.lower()
    notes: list[str] = []
    data: dict = {}
    pitcher_words = re.search(
        r"\b(pitchers?|relievers?|reliever|bullpen|closer|starters?|starting pitcher|sp|rp|arms?)\b", q
    )
    if re.search(r"\b(relievers?|bullpen|closer|rp|setup)\b", q):
        data["roles"] = ["RP"]
    elif re.search(r"\b(starters?|starting pitchers?|rotation|sp)\b", q):
        data["roles"] = ["SP"]
    if pitcher_words:
        data["group"] = "pitcher"
    positions = [code for pat, code in _POSITION_WORDS.items() if re.search(pat, q)]
    if positions and not pitcher_words:
        data["positions"] = positions
        data["group"] = "hitter"
    lefty = re.search(r"\b(lefty|left.handed|lhp|southpaw|lefties)\b", q)
    righty = re.search(r"\b(righty|right.handed|rhp|righties)\b", q)
    hand_key = "throws" if data.get("group") == "pitcher" else "bats"
    if lefty:
        data[hand_key] = ["L"] + (["S"] if hand_key == "bats" else [])
    elif righty:
        data[hand_key] = ["R"]
    if re.search(r"\bswitch.hitt", q):
        data["bats"] = ["S"]
    m = re.search(
        r"(?:under|below|less than|max(?:imum)?|<=?|≤|cheaper than|no more than)\s*\$?\s*(\d+(?:\.\d+)?)\s*(m|mm|million)?",
        q,
    )
    if m and ("$" in q or m.group(2) or "million" in q):
        data["salary_max"] = float(m.group(1))
    if re.search(r"\b(cheap|bargain|league min|min(imum)? salary)\b", q) and "salary_max" not in data:
        data["salary_max"] = 2.0
        notes.append("“cheap” read as ≤ $2M")
    m = re.search(r"(?:under|younger than|below)\s+(\d{2})\b(?!\s*(?:m|mm|million))", q)
    if m and "$" not in q[max(0, m.start() - 2) : m.end()]:
        data["age_max"] = int(m.group(1)) - 1
    if re.search(r"\byoung\b", q) and "age_max" not in data:
        data["age_max"] = 26
        notes.append("“young” read as age ≤ 26")
    m = re.search(r"(\d+)\+?\s*(?:years?|yrs?) (?:of )?(?:control|club control|team control)", q)
    if m:
        data["control_min_years"] = int(m.group(1))
    elif re.search(r"\b(controllable|long.term|team control|club control)\b", q):
        data["control_min_years"] = 3
        notes.append("“controllable” read as 3+ years")
    ratings: dict[str, int] = {}
    elite = re.search(r"\b(elite|best|top|plus.plus)\b", q)
    # "Control" usually means contract control; only skill phrases count as the Control rating.
    skill_control = re.search(r"\bcommand\b|control pitcher|pinpoint control|good control|plus control", q)
    q_skills = re.sub(r"\bcontrol(lable)?\b", " ", q) + (" command" if skill_control else "")
    for pat, (key, floor) in _RATING_WORDS.items():
        if re.search(pat, q_skills):
            if key in ("stuff", "velocity", "control", "contact_mgmt", "stamina") and data.get("group") == "hitter":
                continue
            if key in ("power", "contact", "speed", "glove", "eye") and data.get("group") == "pitcher":
                continue
            ratings[key] = floor + (6 if elite else 0)
    if ratings:
        if data.get("positions") == ["C"] and ratings.pop("glove", None) is not None:
            notes.append("Catcher defense (framing/blocking) isn't in the dataset yet; ignored")
    if ratings:
        data["ratings_min"] = ratings
    pcts: dict[str, float] = {}
    for pat, key in _PERCENTILE_WORDS.items():
        if re.search(pat, q):
            pcts[key] = 90 if elite else 75
    if pcts:
        data["percentiles_min"] = pcts
    archetypes = [aid for aid, label in ARCHETYPE_LABELS.items() if label.lower() in q]
    if archetypes:
        data["archetypes"] = archetypes
    if re.search(r"\b(value|bargain|surplus)\b", q):
        data["sort"] = "surplus"
    if not data:
        notes.append("No recognised constraints; showing top players by sWAR")
    return SearchFilters(**data), notes
