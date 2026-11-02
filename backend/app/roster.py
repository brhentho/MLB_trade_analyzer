"""Roster construction and trade math. Deterministic: no LLM involved."""

from __future__ import annotations

from .search import OF, control_years

LINEUP_SLOTS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
TARGET_SP = 5
TARGET_RP = 8
WEAK_STARTER_WAR = 1.0


def payroll_by_year(players: list[dict]) -> dict[int, float]:
    out: dict[int, float] = {}
    for p in players:
        for y in p["contract"]["years"]:
            out[y["year"]] = round(out.get(y["year"], 0.0) + y["salary"], 2)
    return dict(sorted(out.items()))


def depth_chart(players: list[dict]) -> dict:
    hitters = sorted((p for p in players if p["group"] == "hitter"), key=lambda p: -p["war"])
    pitchers = [p for p in players if p["group"] == "pitcher"]
    slots: dict[str, dict | None] = {s: None for s in LINEUP_SLOTS}
    used: set[int] = set()
    # Pass 1: primary position. Pass 2: OF/IF flexibility. Pass 3: best remaining bat at DH.
    for p in hitters:
        pos = p["position"]
        if pos in slots and slots[pos] is None:
            slots[pos] = p
            used.add(p["id"])
    for p in hitters:
        if p["id"] in used:
            continue
        flex = [s for s in ("LF", "CF", "RF") if p["position"] in OF | {"OF"}] or [
            s for s in ("1B", "3B", "2B") if p["position"] in {"SS", "2B", "3B", "IF"}
        ]
        for s in flex:
            if slots[s] is None:
                slots[s] = p
                used.add(p["id"])
                break
    if slots["DH"] is None:
        for p in hitters:
            if p["id"] not in used:
                slots["DH"] = p
                used.add(p["id"])
                break
    bench = [p for p in hitters if p["id"] not in used]
    rotation = sorted((p for p in pitchers if p["role"] == "SP"), key=lambda p: -p["war"])
    bullpen = sorted((p for p in pitchers if p["role"] == "RP"), key=lambda p: -p["war"])
    # Overflow starters pitch in relief.
    bullpen = bullpen + rotation[TARGET_SP:]
    rotation = rotation[:TARGET_SP]
    return {"lineup": slots, "bench": bench, "rotation": rotation, "bullpen": bullpen}


def needs(chart: dict) -> list[dict]:
    out = []
    for slot, p in chart["lineup"].items():
        if p is None:
            out.append({"slot": slot, "severity": "empty", "message": f"No {slot} on the roster"})
        elif p["war"] < WEAK_STARTER_WAR:
            out.append(
                {
                    "slot": slot,
                    "severity": "weak",
                    "message": f"{slot}: {p['name']} projects as a below-average regular",
                }
            )
    if len(chart["rotation"]) < TARGET_SP:
        out.append(
            {
                "slot": "SP",
                "severity": "empty",
                "message": f"Rotation has {len(chart['rotation'])} of {TARGET_SP} starters",
            }
        )
    else:
        weak = [p for p in chart["rotation"] if p["war"] < WEAK_STARTER_WAR]
        if weak:
            out.append({"slot": "SP", "severity": "weak", "message": f"{len(weak)} rotation spot(s) below average"})
    if len(chart["bullpen"]) < TARGET_RP:
        out.append(
            {
                "slot": "RP",
                "severity": "empty",
                "message": f"Bullpen has {len(chart['bullpen'])} of {TARGET_RP} relievers",
            }
        )
    return out


def active_roster(chart: dict) -> list[dict]:
    """The 26 players who would make the club: 9 starters, best 4 bench bats, 5 SP, 8 RP."""
    lineup = [p for p in chart["lineup"].values() if p is not None]
    return lineup + chart["bench"][:4] + chart["rotation"][:TARGET_SP] + chart["bullpen"][:TARGET_RP]


def evaluate_roster(players: list[dict], plan_season: int, cbt: float, budget: float | None) -> dict:
    chart = depth_chart(players)
    payroll = payroll_by_year(players)
    now = payroll.get(plan_season, 0.0)
    expiring = [p for p in players if p["contract"]["control_through"] == plan_season]
    active = active_roster(chart)
    return {
        "count": len(players),
        "payroll": payroll,
        "payroll_now": now,
        "cbt_threshold": cbt,
        "cbt_room": round(cbt - now, 2),
        "budget": budget,
        "budget_room": round(budget - now, 2) if budget is not None else None,
        "active_count": len(active),
        "war": round(sum(p["war"] for p in active), 1),
        "proj_war": round(sum(p["proj_war"][0] for p in active if p["proj_war"]), 1),
        "surplus": round(sum(p["surplus"] for p in players), 1),
        "depth": {
            "lineup": {k: (v["id"] if v else None) for k, v in chart["lineup"].items()},
            "bench": [p["id"] for p in chart["bench"]],
            "rotation": [p["id"] for p in chart["rotation"]],
            "bullpen": [p["id"] for p in chart["bullpen"]],
        },
        "needs": needs(chart),
        "expiring": [p["id"] for p in expiring],
    }


def side_summary(players: list[dict], plan_season: int) -> dict:
    return {
        "players": [p["id"] for p in players],
        "surplus": round(sum(p["surplus"] for p in players), 1),
        "war": round(sum(p["war"] for p in players), 1),
        "proj_war_next": round(sum(p["proj_war"][0] for p in players if p["proj_war"]), 1),
        "salary_now": round(sum(p["contract"]["salary_now"] for p in players), 2),
        "payroll": payroll_by_year(players),
        "control_years": sum(control_years(p, plan_season) for p in players),
        "unverified_contracts": [p["id"] for p in players if not p["contract"]["verified"]],
    }


def grade_for(fairness: int) -> str:
    for floor, g in (
        (90, "A"),
        (82, "A-"),
        (75, "B+"),
        (68, "B"),
        (60, "B-"),
        (52, "C+"),
        (45, "C"),
        (38, "C-"),
        (30, "D"),
    ):
        if fairness >= floor:
            return g
    return "F"


def evaluate_trade(a_gets: list[dict], b_gets: list[dict], plan_season: int) -> dict:
    a = side_summary(a_gets, plan_season)
    b = side_summary(b_gets, plan_season)
    va, vb = a["surplus"], b["surplus"]
    diff = va - vb
    fairness = int(round(100 * (1 - abs(diff) / (abs(va) + abs(vb) + 20))))
    fairness = max(0, min(100, fairness))
    winner = "even" if abs(diff) < 10 else ("team_a" if diff > 0 else "team_b")
    years = sorted(set(a["payroll"]) | set(b["payroll"]))
    payroll_delta_a = {y: round(a["payroll"].get(y, 0) - b["payroll"].get(y, 0), 2) for y in years}
    return {
        "fairness_score": fairness,
        "grade": grade_for(fairness),
        "winner": winner,
        "surplus_diff": round(diff, 1),
        "team_a": a,
        "team_b": b,
        "payroll_delta_team_a": payroll_delta_a,
    }
