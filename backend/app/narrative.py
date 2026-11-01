"""Template narrative used when no LLM is configured (or it fails)."""

from __future__ import annotations

from .schemas import TradeNarrative


def _names(players: list[dict]) -> str:
    return ", ".join(p["name"] for p in players)


def _side(team: str, gets: list[dict], gives: list[dict], side: dict, other: dict, plan: int) -> str:
    delta = side["salary_now"] - other["salary_now"]
    money = f"adds ${delta:.1f}M" if delta > 0 else f"saves ${-delta:.1f}M"
    return (
        f"{team} receive {_names(gets)} for {_names(gives)}: {side['surplus']:+.1f}M surplus value, "
        f"{side['proj_war_next']:.1f} projected sWAR in {plan} and {side['control_years']} total control years. "
        f"Taking these salaries {money} of {plan} payroll."
    )


def rules_narrative(
    team_a: str, team_b: str, a_gets: list[dict], b_gets: list[dict], result: dict, plan: int
) -> TradeNarrative:
    a, b = result["team_a"], result["team_b"]
    if result["winner"] == "even":
        lead = f"Close to even: the surplus value gap is only ${abs(result['surplus_diff']):.1f}M."
    else:
        win = team_a if result["winner"] == "team_a" else team_b
        lead = f"{win} come out ahead by about ${abs(result['surplus_diff']):.1f}M in surplus value."
    risks: list[str] = []
    for p in a_gets + b_gets:
        if p["age"] >= 32:
            risks.append(f"{p['name']} is {p['age']}; decline risk is built into projections but could be steeper.")
        if not p["contract"]["verified"]:
            risks.append(f"{p['name']}'s salary is an estimate ({p['contract']['status']}); confirm before acting.")
        if p["group"] == "hitter" and p["stats"].get("pa", 0) < 250:
            risks.append(f"{p['name']} has a small {p['stats'].get('pa', 0)} PA sample in the stats season.")
        if p["group"] == "pitcher" and (p["stats"].get("ip") or 0) < 40:
            risks.append(f"{p['name']} threw only {p['stats'].get('ip') or 0} IP in the stats season.")
    if result["fairness_score"] >= 75:
        rec = "Accept: value is balanced; decide on roster fit and payroll timing."
    elif result["fairness_score"] >= 50:
        side = team_b if result["winner"] == "team_a" else team_a
        rec = f"Negotiate: {side} should ask for an additional piece to close the gap."
    else:
        side = team_b if result["winner"] == "team_a" else team_a
        rec = f"Reject as proposed: {side} gives up far more value than it receives."
    return TradeNarrative(
        summary=f"{lead} Grade {result['grade']} (fairness {result['fairness_score']}/100).",
        team_a_analysis=_side(team_a, a_gets, b_gets, a, b, plan),
        team_b_analysis=_side(team_b, b_gets, a_gets, b, a, plan),
        risks=risks[:6] or ["No major data-quality or age flags on the players involved."],
        recommendation=rec,
    )
