"""Request / response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SortKey = Literal["war", "ovr", "pot", "surplus", "value", "age", "salary"]


class SearchFilters(BaseModel):
    """Structured player search. Every field is optional and ANDed together."""

    group: Literal["hitter", "pitcher"] | None = None
    positions: list[str] | None = Field(None, description="C, 1B, 2B, 3B, SS, LF, CF, RF, DH, OF, IF")
    roles: list[Literal["SP", "RP"]] | None = None
    bats: list[Literal["L", "R", "S"]] | None = None
    throws: list[Literal["L", "R"]] | None = None
    teams: list[str] | None = None
    age_min: int | None = Field(None, ge=16, le=50)
    age_max: int | None = Field(None, ge=16, le=50)
    archetypes: list[str] | None = None
    ratings_min: dict[str, int] | None = None
    ratings_max: dict[str, int] | None = None
    percentiles_min: dict[str, float] | None = None
    salary_max: float | None = Field(None, description="Planning-season salary, $M")
    control_min_years: int | None = Field(None, ge=1, le=15)
    war_min: float | None = None
    verified_only: bool = False
    sort: SortKey | str = "war"
    descending: bool = True
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class NaturalSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=300)
    limit: int = Field(25, ge=1, le=100)


class RosterRequest(BaseModel):
    player_ids: list[int] = Field(..., max_length=60)
    budget: float | None = Field(None, description="Payroll budget for the planning season, $M")


class TradeRequest(BaseModel):
    team_a: str = Field(..., max_length=40)
    team_b: str = Field(..., max_length=40)
    team_a_receives: list[int] = Field(..., min_length=1, max_length=12)
    team_b_receives: list[int] = Field(..., min_length=1, max_length=12)
    context: str | None = Field(None, max_length=600)
    use_ai: bool = True


class LegacyTradeProposal(BaseModel):
    """Original /api/evaluate payload: free-text player names."""

    team_a: str = Field(..., max_length=40)
    team_a_gets: list[str] = Field(..., min_length=1, max_length=12)
    team_b: str = Field(..., max_length=40)
    team_b_gets: list[str] = Field(..., min_length=1, max_length=12)
    context: str | None = Field(None, max_length=600)


class ShapeRequest(BaseModel):
    group: Literal["hitter", "pitcher"]
    profile: dict[str, int] = Field(..., min_length=1)
    limit: int = Field(12, ge=1, le=50)


class TradeNarrative(BaseModel):
    summary: str
    team_a_analysis: str
    team_b_analysis: str
    risks: list[str]
    recommendation: str
