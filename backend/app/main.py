"""StatSlugger API."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

from . import llm, model, roster, search  # noqa: E402
from .config import get_settings  # noqa: E402
from .narrative import rules_narrative  # noqa: E402
from .ratelimit import ai_rate_limit  # noqa: E402
from .schemas import (  # noqa: E402
    LegacyTradeProposal,
    NaturalSearchRequest,
    RosterRequest,
    SearchFilters,
    ShapeRequest,
    TradeRequest,
)
from .store import get_store  # noqa: E402

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("statslugger")

COMPACT_FIELDS = (
    "id",
    "name",
    "team",
    "team_id",
    "group",
    "position",
    "role",
    "bats",
    "throws",
    "age",
    "ratings",
    "ovr",
    "pot",
    "war",
    "surplus",
    "archetypes",
    "map",
)


def compact(p: dict) -> dict:
    out = {k: p.get(k) for k in COMPACT_FIELDS}
    c = p["contract"]
    out["contract"] = {k: c[k] for k in ("status", "salary_now", "aav", "control_through", "verified")}
    out["proj_war"] = p["proj_war"][0] if p["proj_war"] else None
    return out


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="StatSlugger API", version="0.2.0", description="Build real MLB rosters with real stats and contracts."
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):  # pragma: no cover - safety net
        rid = uuid.uuid4().hex[:8]
        logger.exception("Unhandled error %s on %s", rid, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal error", "request_id": rid})

    def store():
        return get_store()

    def player_or_404(pid: int) -> dict:
        p = store().by_id.get(pid)
        if not p:
            raise HTTPException(status_code=404, detail="Player not found")
        return p

    def team_or_404(key: str) -> dict:
        t = store().team(key)
        if not t:
            raise HTTPException(status_code=404, detail="Team not found")
        return t

    @app.get("/")
    async def root():
        return {"service": "StatSlugger API", "status": "ok", "version": app.version}

    @app.get("/api/health")
    async def health():
        s = store()
        return {
            "status": "healthy",
            "players": len(s.players),
            "ai_available": settings.openai_configured,
            "model": settings.openai_model if settings.openai_configured else None,
        }

    @app.get("/api/meta")
    async def meta():
        s = store()
        return {
            **s.meta,
            "ai_available": settings.openai_configured,
            "ratings": {
                "hitter": list(model.HITTER_RATINGS),
                "pitcher": list(model.PITCHER_RATINGS),
                "labels": model.RATING_LABELS,
            },
            "percentile_labels": search.PERCENTILE_LABELS,
        }

    @app.get("/api/teams")
    async def teams():
        s = store()
        plan = s.meta["plan_season"]
        return [{**t, "payroll_now": t["payroll"].get(str(plan), t["payroll"].get(plan, 0))} for t in s.teams]

    @app.get("/api/teams/{key}/roster")
    async def team_roster(key: str):
        s = store()
        t = team_or_404(key)
        players = s.roster(t["id"])
        evaluation = roster.evaluate_roster(players, s.meta["plan_season"], settings.cbt_threshold, None)
        return {"team": t, "players": players, "evaluation": evaluation}

    @app.get("/api/players")
    async def list_players(
        group: Literal["hitter", "pitcher"] | None = None,
        team: str | None = None,
        mapped: bool = False,
        limit: int = Query(2000, ge=1, le=2000),
    ):
        s = store()
        tid = team_or_404(team)["id"] if team else None
        out = [
            compact(p)
            for p in s.players
            if (group is None or p["group"] == group)
            and (tid is None or p["team_id"] == tid)
            and (not mapped or p.get("map"))
        ]
        return out[:limit]

    @app.get("/api/players/{pid}")
    async def get_player(pid: int):
        return player_or_404(pid)

    @app.get("/api/players/{pid}/similar")
    async def similar_players(
        pid: int,
        limit: int = Query(10, ge=1, le=50),
        salary_max: float | None = None,
        control_min_years: int | None = None,
    ):
        target = player_or_404(pid)
        s = store()
        results = search.similar(target, s.players, limit, s.meta["plan_season"], salary_max, control_min_years)
        return {"target": target, "results": results}

    @app.post("/api/players/search")
    async def search_players(filters: SearchFilters):
        s = store()
        return {
            "filters": filters.model_dump(exclude_none=True),
            **search.search(s.players, filters, s.meta["plan_season"]),
        }

    @app.post("/api/players/search/natural")
    async def natural_search(body: NaturalSearchRequest, request: Request):
        s = store()
        filters, notes, source = None, [], "rules"
        if settings.openai_configured:
            ai_rate_limit(request)
            filters = await llm.parse_search(body.query, [a[0] for a in model.ARCHETYPES])
            source = "ai" if filters else "rules"
        if filters is None:
            filters, notes = search.parse_query(body.query)
        filters.limit = body.limit
        result = search.search(s.players, filters, s.meta["plan_season"])
        return {
            "query": body.query,
            "interpreted_by": source,
            "notes": notes,
            "filters": filters.model_dump(
                exclude_none=True, exclude={"limit", "offset", "descending", "verified_only"}
            ),
            **result,
        }

    @app.post("/api/players/shape")
    async def shape_search(body: ShapeRequest):
        allowed = set(model.HITTER_RATINGS if body.group == "hitter" else model.PITCHER_RATINGS)
        profile = {k: v for k, v in body.profile.items() if k in allowed}
        if not profile:
            raise HTTPException(status_code=422, detail="Profile has no ratings for this group")
        return {
            "profile": profile,
            "results": search.nearest_to_profile(profile, store().players, body.group, body.limit),
        }

    @app.get("/api/archetypes")
    async def archetypes():
        s = store()
        counts: dict[str, int] = {}
        for p in s.players:
            for a in p["archetypes"]:
                counts[a] = counts.get(a, 0) + 1
        return [
            {
                "id": a[0],
                "label": a[1],
                "group": a[2],
                "description": a[3],
                "profile": a[5],
                "count": counts.get(a[0], 0),
            }
            for a in model.ARCHETYPES
        ]

    @app.post("/api/rosters/evaluate")
    async def evaluate_roster(body: RosterRequest):
        s = store()
        missing = [pid for pid in body.player_ids if pid not in s.by_id]
        if missing:
            raise HTTPException(status_code=404, detail=f"Unknown player ids: {missing[:5]}")
        players = [s.by_id[pid] for pid in dict.fromkeys(body.player_ids)]
        return roster.evaluate_roster(players, s.meta["plan_season"], settings.cbt_threshold, body.budget)

    async def _trade(
        team_a: str,
        team_b: str,
        a_gets: list[dict],
        b_gets: list[dict],
        context: str | None,
        use_ai: bool,
        request: Request,
        unknown: list[str] | None = None,
    ) -> dict:
        s = store()
        plan = s.meta["plan_season"]
        result = roster.evaluate_trade(a_gets, b_gets, plan)
        narrative, source = None, "rules"
        if use_ai and settings.openai_configured:
            ai_rate_limit(request)
            facts = {
                "plan_season": plan,
                "dollars_per_war_m": settings.dollars_per_war,
                "context": context,
                "team_a": team_a,
                "team_b": team_b,
                "team_a_receives": [_fact(p) for p in a_gets],
                "team_b_receives": [_fact(p) for p in b_gets],
                "computed": result,
                "unrecognised_names": unknown or [],
            }
            narrative = await llm.trade_narrative(facts)
            source = "ai" if narrative else "rules"
        if narrative is None:
            narrative = rules_narrative(team_a, team_b, a_gets, b_gets, result, plan)
        if unknown:
            narrative.risks.insert(0, f"Not found in the player database (ignored in the math): {', '.join(unknown)}")
        return {
            **result,
            **narrative.model_dump(),
            "narrative_source": source,
            "team_a_name": team_a,
            "team_b_name": team_b,
            "team_a_players": [compact(p) for p in a_gets],
            "team_b_players": [compact(p) for p in b_gets],
        }

    @app.post("/api/trades/evaluate")
    async def evaluate_trade(body: TradeRequest, request: Request):
        s = store()
        ids = body.team_a_receives + body.team_b_receives
        missing = [pid for pid in ids if pid not in s.by_id]
        if missing:
            raise HTTPException(status_code=404, detail=f"Unknown player ids: {missing[:5]}")
        a_name = (s.team(body.team_a) or {}).get("name", body.team_a)
        b_name = (s.team(body.team_b) or {}).get("name", body.team_b)
        return await _trade(
            a_name,
            b_name,
            [s.by_id[i] for i in body.team_a_receives],
            [s.by_id[i] for i in body.team_b_receives],
            body.context,
            body.use_ai,
            request,
        )

    @app.post("/api/evaluate", deprecated=True)
    async def legacy_evaluate(body: LegacyTradeProposal, request: Request):
        """Backwards-compatible free-text endpoint; resolves names against the player database."""
        s = store()
        unknown: list[str] = []

        def resolve(names: list[str]) -> list[dict]:
            out = []
            for n in names:
                p = s.find_by_name(n)
                if p:
                    out.append(p)
                else:
                    unknown.append(n)
            return out

        a_gets, b_gets = resolve(body.team_a_gets), resolve(body.team_b_gets)
        if not a_gets or not b_gets:
            raise HTTPException(
                status_code=422, detail=f"Could not match players on both sides. Unrecognised: {', '.join(unknown)}"
            )
        return await _trade(body.team_a, body.team_b, a_gets, b_gets, body.context, True, request, unknown)

    return app


def _fact(p: dict) -> dict:
    c = p["contract"]
    return {
        "name": p["name"],
        "team": p["team"],
        "position": p["position"],
        "role": p["role"],
        "age": p["age"],
        "swar_last": p["war"],
        "proj_swar": p["proj_war"],
        "ratings": p["ratings"],
        "ovr": p["ovr"],
        "contract": {"status": c["status"], "verified": c["verified"], "salaries": c["years"], "notes": c["notes"]},
        "surplus_m": p["surplus"],
        "archetypes": p["archetypes"],
    }


app = create_app()
