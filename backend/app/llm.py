"""Optional OpenAI layer. The app is fully functional without it.

The model never produces numbers that drive decisions: it writes prose around
facts computed in roster.py, or translates text into a SearchFilters object
that is validated before use.
"""

from __future__ import annotations

import json
import logging
import os

from pydantic import ValidationError

from .config import get_settings
from .schemas import SearchFilters, TradeNarrative

logger = logging.getLogger(__name__)

TRADE_SYSTEM = """You are an MLB front-office analyst. You are given computed facts about a proposed trade:
surplus value ($M, projected value minus salary over years of control), StatSlugger WAR estimates (sWAR),
salaries, years of control, ratings on the 20-80 scouting scale, and payroll change by season.
Use ONLY these facts plus general baseball reasoning. Do not invent statistics, injuries, or contract terms.
If a contract is marked unverified, say the salary is an estimate. Be specific and concise."""

SEARCH_SYSTEM = """Translate a baseball scouting request into JSON search filters.
Ratings use the 20-80 scouting scale (50 average, 60 plus, 70 plus-plus).
Hitter ratings: contact, power, eye, speed, glove, arm. Pitcher ratings: stuff, contact_mgmt, control, velocity, stamina.
Percentile keys (0-100): xwoba, xba, xslg, brl_percent, exit_velocity, max_ev, hard_hit_percent, k_percent, bb_percent,
whiff_percent, chase_percent, sprint_speed, oaa, arm_strength, bat_speed, squared_up_rate, xera, fb_velocity, fb_spin.
Money is in millions of USD. Archetype ids: {archetypes}.
Only include constraints the user actually asked for. Use null for anything not requested."""


def _client():
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from openai import AsyncOpenAI

    return AsyncOpenAI()


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def _search_schema() -> dict:
    str_list = _nullable({"type": "array", "items": {"type": "string"}})
    int_map = _nullable(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                k: _nullable({"type": "integer"})
                for k in (
                    "contact",
                    "power",
                    "eye",
                    "speed",
                    "glove",
                    "arm",
                    "stuff",
                    "contact_mgmt",
                    "control",
                    "velocity",
                    "stamina",
                )
            },
            "required": [
                "contact",
                "power",
                "eye",
                "speed",
                "glove",
                "arm",
                "stuff",
                "contact_mgmt",
                "control",
                "velocity",
                "stamina",
            ],
        }
    )
    pct_keys = (
        "xwoba",
        "xba",
        "xslg",
        "brl_percent",
        "exit_velocity",
        "max_ev",
        "hard_hit_percent",
        "k_percent",
        "bb_percent",
        "whiff_percent",
        "chase_percent",
        "sprint_speed",
        "oaa",
        "arm_strength",
        "bat_speed",
        "squared_up_rate",
        "xera",
        "fb_velocity",
        "fb_spin",
    )
    pct_map = _nullable(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {k: _nullable({"type": "number"}) for k in pct_keys},
            "required": list(pct_keys),
        }
    )
    props = {
        "group": _nullable({"type": "string", "enum": ["hitter", "pitcher"]}),
        "positions": str_list,
        "roles": str_list,
        "bats": str_list,
        "throws": str_list,
        "age_min": _nullable({"type": "integer"}),
        "age_max": _nullable({"type": "integer"}),
        "archetypes": str_list,
        "ratings_min": int_map,
        "percentiles_min": pct_map,
        "salary_max": _nullable({"type": "number"}),
        "control_min_years": _nullable({"type": "integer"}),
        "war_min": _nullable({"type": "number"}),
        "sort": {"type": "string", "enum": ["war", "ovr", "surplus", "value", "age", "salary"]},
    }
    return {"type": "object", "additionalProperties": False, "properties": props, "required": list(props)}


def _strip_nulls(obj):
    if isinstance(obj, dict):
        cleaned = {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
        return {k: v for k, v in cleaned.items() if v not in ({}, [])}
    return obj


async def parse_search(query: str, archetype_ids: list[str]) -> SearchFilters | None:
    client = _client()
    if client is None:
        return None
    try:
        resp = await client.chat.completions.create(
            model=get_settings().openai_model,
            temperature=0,
            messages=[
                {"role": "system", "content": SEARCH_SYSTEM.format(archetypes=", ".join(archetype_ids))},
                {"role": "user", "content": query},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "filters", "schema": _search_schema(), "strict": True},
            },
        )
        raw = _strip_nulls(json.loads(resp.choices[0].message.content or "{}"))
        return SearchFilters(**raw)
    except (ValidationError, ValueError) as exc:
        logger.warning("LLM search filters rejected: %s", exc)
        return None
    except Exception:  # network, quota, auth
        logger.exception("LLM search parse failed")
        return None


async def trade_narrative(facts: dict) -> TradeNarrative | None:
    client = _client()
    if client is None:
        return None
    schema = TradeNarrative.model_json_schema()
    schema["additionalProperties"] = False
    for attempt in range(2):
        try:
            resp = await client.chat.completions.create(
                model=get_settings().openai_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": TRADE_SYSTEM},
                    {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "trade_narrative", "schema": schema, "strict": True},
                },
            )
            return TradeNarrative.model_validate_json(resp.choices[0].message.content or "{}")
        except ValidationError as exc:
            logger.warning("LLM narrative invalid (attempt %s): %s", attempt + 1, exc)
        except Exception:
            logger.exception("LLM narrative failed")
            return None
    return None
