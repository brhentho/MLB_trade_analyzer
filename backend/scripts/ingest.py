"""Build backend/data/players.json from public MLB data + the curated contract seed.

Sources
  * MLB Stats API (statsapi.mlb.com): teams, 40-man rosters, bio, season stats
  * Baseball Savant: percentile rankings (batters, pitchers), expected stats
  * backend/data/contracts.csv: hand-curated guaranteed contracts

Run from the repo root:
    python backend/scripts/ingest.py            # fetch live
    python backend/scripts/ingest.py --cache    # reuse backend/data/raw/ if present

Standard library only, so it runs anywhere Python 3.11+ does.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
import time
import unicodedata
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import model  # noqa: E402
from app import roster as rosters  # noqa: E402
from app.config import DATA_DIR, Settings, get_settings  # noqa: E402

RAW_DIR = DATA_DIR / "raw"
UA = {"User-Agent": "StatSlugger-ingest/0.2 (personal, non-commercial)"}
COTS_URL = "https://legacy.baseballprospectus.com/compensation/cots/"


def fetch(url: str, name: str, use_cache: bool) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    if use_cache and path.exists():
        return path.read_text(encoding="utf-8")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                text = r.read().decode("utf-8-sig")
            path.write_text(text, encoding="utf-8")
            time.sleep(0.25)
            return text
        except Exception as exc:  # pragma: no cover - network
            if attempt == 2:
                raise
            print(f"  retry {name}: {exc}")
            time.sleep(2)
    raise RuntimeError("unreachable")


def norm_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for token in (".", "'", ",", "-"):
        s = s.replace(token, " " if token == "-" else "")
    return " ".join(w for w in s.split() if w not in {"jr", "sr", "ii", "iii"})


def num(v) -> float | None:
    if v in (None, "", "null"):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def read_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def pct_map(rows: list[dict], skip: set[str]) -> dict[int, dict]:
    out = {}
    for row in rows:
        pid = int(row["player_id"])
        out[pid] = {k: num(v) for k, v in row.items() if k not in skip}
    return out


def season_split(stats: list, group: str) -> dict:
    for block in stats or []:
        if block.get("group", {}).get("displayName") != group:
            continue
        splits = block.get("splits") or []
        mlb = [s for s in splits if s.get("sport", {}).get("id", 1) == 1]
        totals = [s for s in mlb if "team" not in s] or mlb
        if totals:
            return totals[0].get("stat", {})
    return {}


def load_contracts() -> dict[str, dict]:
    out = {}
    with open(DATA_DIR / "contracts.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            start, end = int(row["start_year"]), int(row["end_year"])
            total = float(row["total_usd_m"])
            cbt = num(row.get("cbt_aav_m"))
            out[norm_name(row["name"])] = {
                "name": row["name"],
                "start": start,
                "end": end,
                "total": total,
                "aav": round(cbt if cbt else total / (end - start + 1), 2),
                "notes": row.get("notes") or "",
            }
    return out


def build_contract(person: dict, curated: dict | None, proj_war: list[float], s: Settings) -> dict:
    plan = s.plan_season
    if curated:
        end = curated["end"]
        notes = curated["notes"]
        if end < plan:
            notes = (notes + "; " if notes else "") + f"Guarantee ended {end}; {plan} status not modeled"
            end = plan
            verified = False
        else:
            verified = True
        years = [{"year": y, "salary": curated["aav"]} for y in range(plan, end + 1)]
        return {
            "status": "guaranteed",
            "verified": verified,
            "aav": curated["aav"],
            "salary_now": curated["aav"],
            "years": years,
            "control_through": end,
            "signed": f"{curated['end'] - curated['start'] + 1} yr / ${curated['total']:g}M ({curated['start']}-{curated['end']})",
            "notes": notes,
            "source": COTS_URL,
            "as_of": "2025-04",
        }

    debut = person.get("mlbDebutDate")
    debut_year = int(debut[:4]) if debut else plan
    control_through = debut_year + 6
    years = []
    if control_through >= plan:
        status = "pre-arb"
        for i, y in enumerate(range(plan, control_through + 1)):
            service = y - debut_year - 1
            if service < 3:
                salary = s.league_min
            else:
                arb_share = {3: 0.2, 4: 0.3, 5: 0.45}.get(service, 0.45)
                w = proj_war[i] if i < len(proj_war) else proj_war[-1]
                salary = min(30.0, max(s.league_min * 1.5, arb_share * max(w, 0) * s.dollars_per_war))
                if y == plan:
                    status = "arbitration"
            years.append({"year": y, "salary": round(salary, 2)})
        notes = "Estimated from MLB debut date; service time and arbitration salaries are approximate"
    else:
        status = "estimated"
        control_through = plan
        w = proj_war[0] if proj_war else 0
        years = [{"year": plan, "salary": round(min(30.0, max(1.5, 1.5 + 0.8 * max(w, 0) * s.dollars_per_war)), 2)}]
        notes = "Veteran contract not in curated seed; one-year salary estimated from projected value"
    return {
        "status": status,
        "verified": False,
        "aav": round(sum(y["salary"] for y in years) / len(years), 2),
        "salary_now": years[0]["salary"],
        "years": years,
        "control_through": control_through,
        "signed": None,
        "notes": notes,
        "source": None,
        "as_of": None,
    }


def pca_2d(vectors: list[list[float]]) -> list[tuple[float, float]]:
    """Tiny PCA via power iteration (no numpy dependency)."""
    if not vectors:
        return []
    dims = len(vectors[0])
    means = [sum(v[i] for v in vectors) / len(vectors) for i in range(dims)]
    centered = [[v[i] - means[i] for i in range(dims)] for v in vectors]
    cov = [[sum(r[i] * r[j] for r in centered) / len(centered) for j in range(dims)] for i in range(dims)]

    def power(mat, deflate=None):
        vec = [1.0 / math.sqrt(dims)] * dims
        if deflate:
            vec = [vec[i] + (0.3 if i % 2 else -0.3) for i in range(dims)]
        for _ in range(200):
            nxt = [sum(mat[i][j] * vec[j] for j in range(dims)) for i in range(dims)]
            norm = math.sqrt(sum(x * x for x in nxt)) or 1.0
            vec = [x / norm for x in nxt]
        val = sum(vec[i] * sum(mat[i][j] * vec[j] for j in range(dims)) for i in range(dims))
        return vec, val

    v1, l1 = power(cov)
    cov2 = [[cov[i][j] - l1 * v1[i] * v1[j] for j in range(dims)] for i in range(dims)]
    v2, _ = power(cov2, deflate=True)
    pts = [(sum(r[i] * v1[i] for i in range(dims)), sum(r[i] * v2[i] for i in range(dims))) for r in centered]
    max_x = max(abs(p[0]) for p in pts) or 1
    max_y = max(abs(p[1]) for p in pts) or 1
    return [(round(p[0] / max_x, 3), round(p[1] / max_y, 3)) for p in pts]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", action="store_true", help="reuse raw downloads")
    args = parser.parse_args()
    s = get_settings()
    season = s.stats_season

    print(f"Fetching teams ({season})")
    teams_raw = json.loads(
        fetch(
            f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}&hydrate=league,division",
            "teams.json",
            args.cache,
        )
    )["teams"]
    teams = {
        t["id"]: {
            "id": t["id"],
            "name": t["name"],
            "abbrev": t["abbreviation"],
            "short": t.get("teamName", t["name"]),
            "league": t.get("league", {}).get("abbreviation") or t.get("league", {}).get("name", ""),
            "division": t.get("division", {}).get("nameShort") or t.get("division", {}).get("name", ""),
        }
        for t in teams_raw
    }

    print("Fetching Savant leaderboards")
    bat_pct = pct_map(
        read_csv(
            fetch(
                f"https://baseballsavant.mlb.com/leaderboard/percentile-rankings?type=batter&year={season}&csv=true",
                "savant_batter_pct.csv",
                args.cache,
            )
        ),
        {"player_name", "player_id", "year"},
    )
    pit_pct = pct_map(
        read_csv(
            fetch(
                f"https://baseballsavant.mlb.com/leaderboard/percentile-rankings?type=pitcher&year={season}&csv=true",
                "savant_pitcher_pct.csv",
                args.cache,
            )
        ),
        {"player_name", "player_id", "year"},
    )
    xstats = {
        int(r["player_id"]): r
        for r in read_csv(
            fetch(
                f"https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year={season}"
                "&position=&team=&min=1&csv=true",
                "savant_batter_expected.csv",
                args.cache,
            )
        )
        if num(r.get("woba")) is not None and num(r.get("est_woba")) is not None and num(r.get("pa"))
    }

    tot_pa = sum(int(r["pa"]) for r in xstats.values())
    lg_woba = sum(float(r["woba"]) * int(r["pa"]) for r in xstats.values()) / tot_pa

    roster_entries = []
    for tid in sorted(teams):
        print(f"  roster {teams[tid]['abbrev']}")
        data = json.loads(
            fetch(
                f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=40Man&season={season}"
                f"&hydrate=person(stats(type=season,season={season},group=[hitting,pitching]))",
                f"roster_{tid}.json",
                args.cache,
            )
        )
        for entry in data.get("roster", []):
            roster_entries.append((tid, entry))

    # League pitching constants from everyone we have.
    totals = {"er": 0, "ip": 0.0, "hr": 0, "bb": 0, "hbp": 0, "k": 0}
    for _, entry in roster_entries:
        p = season_split(entry["person"].get("stats"), "pitching")
        ip = model.innings_to_float(p.get("inningsPitched"))
        if ip <= 0:
            continue
        totals["ip"] += ip
        totals["er"] += p.get("earnedRuns", 0)
        totals["hr"] += p.get("homeRuns", 0)
        totals["bb"] += p.get("baseOnBalls", 0)
        totals["hbp"] += p.get("hitByPitch", 0)
        totals["k"] += p.get("strikeOuts", 0)
    lg_era = 9 * totals["er"] / totals["ip"]
    fip_const = lg_era - (13 * totals["hr"] + 3 * (totals["bb"] + totals["hbp"]) - 2 * totals["k"]) / totals["ip"]
    print(f"League wOBA {lg_woba:.3f}, ERA {lg_era:.2f}, FIP constant {fip_const:.2f}")

    contracts = load_contracts()
    matched_contracts: set[str] = set()
    players = []
    for tid, entry in roster_entries:
        person = entry["person"]
        pid = person["id"]
        pos = person.get("primaryPosition", {}).get("abbreviation", "")
        is_pitcher = pos == "P"
        position = "DH" if pos == "TWP" else pos
        age = person.get("currentAge") or 27
        hit = season_split(person.get("stats"), "hitting")
        pit = season_split(person.get("stats"), "pitching")
        extras: dict = {}
        if is_pitcher:
            pct = pit_pct.get(pid, {})
            ratings = model.ratings_from_percentiles(pct, model.PITCHER_INPUTS)
            ip = model.innings_to_float(pit.get("inningsPitched"))
            g, gs = pit.get("gamesPlayed", 0), pit.get("gamesStarted", 0)
            ratings["stamina"] = model.stamina_rating(ip, g, gs)
            starter = g > 0 and gs / g >= 0.5
            role = "SP" if starter else "RP"
            extras["role"] = role
            f = model.fip(
                pit.get("homeRuns", 0),
                pit.get("baseOnBalls", 0),
                pit.get("hitByPitch", 0),
                pit.get("strikeOuts", 0),
                ip,
                fip_const,
            )
            war = model.pitcher_war(f, lg_era, ip, starter)
            sample = min(0.85, ip / (200 if starter else 70)) if ip else 0.0
            bf = pit.get("battersFaced") or 0
            stats = {
                "g": g,
                "gs": gs,
                "ip": round(ip, 1),
                "era": num(pit.get("era")),
                "fip": round(f, 2) if f else None,
                "whip": num(pit.get("whip")),
                "so": pit.get("strikeOuts", 0),
                "bb": pit.get("baseOnBalls", 0),
                "k_pct": round(100 * pit.get("strikeOuts", 0) / bf, 1) if bf else None,
                "bb_pct": round(100 * pit.get("baseOnBalls", 0) / bf, 1) if bf else None,
                "sv": pit.get("saves", 0),
                "hld": pit.get("holds", 0),
                "w": pit.get("wins", 0),
                "l": pit.get("losses", 0),
            }
            rate = war / max(ip, 1) * (180 if starter else 65)
        else:
            pct = bat_pct.get(pid, {})
            ratings = model.ratings_from_percentiles(pct, model.HITTER_INPUTS)
            role = position
            pa = hit.get("plateAppearances", 0)
            x = xstats.get(pid)
            woba = None
            if x:
                woba = 0.5 * float(x["woba"]) + 0.5 * float(x["est_woba"])
            elif pa:
                woba = lg_woba - 0.02
            war = model.hitter_war(woba, lg_woba, pa, position, ratings.get("glove")) if woba else 0.0
            if pos == "TWP" and pit:
                ip = model.innings_to_float(pit.get("inningsPitched"))
                f = model.fip(
                    pit.get("homeRuns", 0),
                    pit.get("baseOnBalls", 0),
                    pit.get("hitByPitch", 0),
                    pit.get("strikeOuts", 0),
                    ip,
                    fip_const,
                )
                war = round(war + model.pitcher_war(f, lg_era, ip, True), 1)
            sample = min(0.85, pa / 700) if pa else 0.0
            stats = {
                "g": hit.get("gamesPlayed", 0),
                "pa": pa,
                "hr": hit.get("homeRuns", 0),
                "r": hit.get("runs", 0),
                "rbi": hit.get("rbi", 0),
                "sb": hit.get("stolenBases", 0),
                "avg": num(hit.get("avg")),
                "obp": num(hit.get("obp")),
                "slg": num(hit.get("slg")),
                "ops": num(hit.get("ops")),
                "woba": num(x["woba"]) if x else None,
                "xwoba": num(x["est_woba"]) if x else None,
                "k_pct": round(100 * hit.get("strikeOuts", 0) / pa, 1) if pa else None,
                "bb_pct": round(100 * hit.get("baseOnBalls", 0) / pa, 1) if pa else None,
            }
            rate = war / max(pa, 1) * 650

        key = norm_name(person["fullName"])
        curated = contracts.get(key)
        if curated:
            matched_contracts.add(key)
        horizon = 6
        proj = model.project_war(war, age, horizon, is_pitcher, sample)
        contract = build_contract(person, curated, proj, s)
        n_years = len(contract["years"])
        proj = model.project_war(war, age, max(n_years, 1), is_pitcher, sample)
        surplus = model.surplus_value(proj, [y["salary"] for y in contract["years"]], s.dollars_per_war)

        players.append(
            {
                "id": pid,
                "name": person["fullName"],
                "team_id": tid,
                "team": teams[tid]["abbrev"],
                "group": "pitcher" if is_pitcher else "hitter",
                "position": "P" if is_pitcher else position,
                "role": role,
                "two_way": pos == "TWP",
                "bats": person.get("batSide", {}).get("code"),
                "throws": person.get("pitchHand", {}).get("code"),
                "age": age,
                "debut": person.get("mlbDebutDate"),
                "status": entry.get("status", {}).get("description"),
                "ratings": ratings,
                "percentiles": {k: v for k, v in pct.items() if v is not None},
                "stats": stats,
                "war": war,
                "proj_war": proj,
                "contract": contract,
                "surplus": surplus,
                "archetypes": model.archetypes_for(ratings, "pitcher" if is_pitcher else "hitter", extras),
                "_rate": rate,
                "_sample": sample,
            }
        )

    # Overall / potential on the 20-80 scale, ranked within hitters / SP / RP.
    for bucket in ("hitter", "SP", "RP"):
        group = [
            p
            for p in players
            if (p["group"] == "hitter") == (bucket == "hitter") and (bucket == "hitter" or p["role"] == bucket)
        ]
        shrunk = [(p, p["_sample"] * p["_rate"] + (1 - p["_sample"]) * 0.5) for p in group]
        ordered = sorted(v for _, v in shrunk)
        for p, v in shrunk:
            rank = sum(1 for o in ordered if o < v) + 0.5 * sum(1 for o in ordered if o == v)
            pct = 100 * rank / max(len(ordered), 1)
            ovr = model.percentile_to_scout(pct)
            bonus = 10 if p["age"] <= 23 else 6 if p["age"] <= 25 else 3 if p["age"] <= 27 else 0
            p["ovr"] = ovr
            p["pot"] = min(80, max(ovr, ovr + bonus if p["_sample"] < 0.6 else ovr + bonus // 2))

    # Skill-space map coordinates for the constellation view.
    for group, keys in (("hitter", model.HITTER_RATINGS), ("pitcher", model.PITCHER_RATINGS)):
        members = [
            p for p in players if p["group"] == group and sum(1 for k in keys if p["ratings"].get(k) is not None) >= 3
        ]
        coords = pca_2d([[p["ratings"].get(k) or 50 for k in keys] for p in members])
        for p, (x, y) in zip(members, coords, strict=True):
            p["map"] = {"x": x, "y": y}
    for p in players:
        p.setdefault("map", None)
        p.pop("_rate")
        p.pop("_sample")

    for tid in teams:
        roster = [p for p in players if p["team_id"] == tid]
        by_year = {}
        for p in roster:
            for y in p["contract"]["years"]:
                by_year[y["year"]] = round(by_year.get(y["year"], 0) + y["salary"], 2)
        teams[tid]["payroll"] = by_year
        teams[tid]["war"] = round(sum(p["war"] for p in rosters.active_roster(rosters.depth_chart(roster))), 1)

    unmatched = sorted(c["name"] for k, c in contracts.items() if k not in matched_contracts)
    out = {
        "meta": {
            "stats_season": season,
            "plan_season": s.plan_season,
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "league": {"woba": round(lg_woba, 3), "era": round(lg_era, 2), "fip_constant": round(fip_const, 2)},
            "assumptions": {
                "dollars_per_war_m": s.dollars_per_war,
                "league_min_m": s.league_min,
                "cbt_threshold_m": s.cbt_threshold,
                "war": "StatSlugger estimate (sWAR): wOBA/xwOBA batting runs + positional + OAA proxy; FIP-based for pitchers",
            },
            "sources": [
                "MLB Stats API (statsapi.mlb.com)",
                "Baseball Savant percentile rankings and expected statistics",
                "Curated contracts seed (backend/data/contracts.csv), reference: Cot's Baseball Contracts",
            ],
            "curated_contracts_unmatched": unmatched,
            "date": date.today().isoformat(),
        },
        "teams": sorted(teams.values(), key=lambda t: t["name"]),
        "players": sorted(players, key=lambda p: -p["war"]),
    }
    (DATA_DIR / "players.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(players)} players, {len(teams)} teams. Unmatched curated contracts: {unmatched}")


if __name__ == "__main__":
    main()
