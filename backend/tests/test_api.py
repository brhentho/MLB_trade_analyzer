import json
from types import SimpleNamespace

from app import llm


def test_health_and_meta(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["players"] > 500
    meta = client.get("/api/meta").json()
    assert meta["plan_season"] == meta["stats_season"] + 1
    assert meta["ai_available"] is False


def test_teams_and_roster(client):
    teams = client.get("/api/teams").json()
    assert len(teams) == 30
    r = client.get(f"/api/teams/{teams[0]['abbrev']}/roster").json()
    assert r["players"] and set(r["evaluation"]["depth"]["lineup"]) >= {"C", "SS", "DH"}
    assert client.get("/api/teams/XXX/roster").status_code == 404


def test_player_endpoints(client, store):
    pid = store.players[0]["id"]
    assert client.get(f"/api/players/{pid}").json()["id"] == pid
    assert client.get("/api/players/1").status_code == 404
    sim = client.get(f"/api/players/{pid}/similar?limit=5").json()
    assert len(sim["results"]) == 5
    assert all(r["player"]["group"] == store.players[0]["group"] for r in sim["results"])
    compact = client.get("/api/players?group=pitcher&mapped=true").json()
    assert compact and all(p["group"] == "pitcher" and p["map"] for p in compact)
    assert "percentiles" not in compact[0]


def test_search_and_natural(client):
    r = client.post("/api/players/search", json={"group": "hitter", "positions": ["SS"], "limit": 5}).json()
    assert r["total"] >= 5 and len(r["results"]) == 5
    wars = [x["player"]["war"] for x in r["results"]]
    assert wars == sorted(wars, reverse=True)
    n = client.post("/api/players/search/natural", json={"query": "lefty reliever under $5M"}).json()
    assert n["interpreted_by"] == "rules"
    assert n["filters"]["throws"] == ["L"]
    assert all(x["player"]["throws"] == "L" and x["player"]["role"] == "RP" for x in n["results"])


def test_shape_search(client):
    r = client.post("/api/players/shape", json={"group": "hitter", "profile": {"speed": 75, "power": 40}}).json()
    assert r["results"] and r["results"][0]["similarity"] >= r["results"][-1]["similarity"]
    assert client.post("/api/players/shape", json={"group": "hitter", "profile": {"stuff": 70}}).status_code == 422


def test_archetypes(client):
    arch = client.get("/api/archetypes").json()
    assert {"slugger", "high-leverage"} <= {a["id"] for a in arch}


def test_roster_evaluate(client, store):
    ids = [p["id"] for p in store.players[:30]]
    r = client.post("/api/rosters/evaluate", json={"player_ids": ids, "budget": 200}).json()
    assert r["count"] == 30 and r["budget_room"] == round(200 - r["payroll_now"], 2)
    assert r["active_count"] <= 26
    assert client.post("/api/rosters/evaluate", json={"player_ids": [1]}).status_code == 404


def test_trade_rules_narrative(client, store):
    a, b = store.players[0], store.players[-1]
    r = client.post(
        "/api/trades/evaluate",
        json={"team_a": b["team"], "team_b": a["team"], "team_a_receives": [a["id"]], "team_b_receives": [b["id"]]},
    ).json()
    assert r["narrative_source"] == "rules"
    assert r["winner"] == "team_a"
    assert 0 <= r["fairness_score"] <= 100 and r["grade"]
    assert r["summary"] and r["risks"]


def test_legacy_evaluate(client, store):
    a, b = store.players[0], store.players[1]
    r = client.post(
        "/api/evaluate",
        json={"team_a": "X", "team_a_gets": [a["name"], "Nobody Real"], "team_b": "Y", "team_b_gets": [b["name"]]},
    )
    assert r.status_code == 200
    assert "Nobody Real" in r.json()["risks"][0]
    bad = client.post(
        "/api/evaluate", json={"team_a": "X", "team_a_gets": ["Zzz"], "team_b": "Y", "team_b_gets": ["Qqq"]}
    )
    assert bad.status_code == 422


def test_trade_uses_ai_when_configured(client, store, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    payload = {"summary": "s", "team_a_analysis": "a", "team_b_analysis": "b", "risks": ["r"], "recommendation": "x"}

    class FakeCompletions:
        async def create(self, **kwargs):
            assert kwargs["response_format"]["type"] == "json_schema"
            facts = json.loads(kwargs["messages"][1]["content"])
            assert "computed" in facts
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])

    monkeypatch.setattr(llm, "_client", lambda: SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())))
    from fastapi.testclient import TestClient

    from app.main import create_app

    c = TestClient(create_app())
    a, b = store.players[0], store.players[1]
    r = c.post(
        "/api/trades/evaluate",
        json={"team_a": "SEA", "team_b": "NYY", "team_a_receives": [a["id"]], "team_b_receives": [b["id"]]},
    ).json()
    assert r["narrative_source"] == "ai" and r["summary"] == "s"


def test_ai_failure_falls_back(client, store, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    class Boom:
        async def create(self, **kwargs):
            raise RuntimeError("quota")

    monkeypatch.setattr(llm, "_client", lambda: SimpleNamespace(chat=SimpleNamespace(completions=Boom())))
    from fastapi.testclient import TestClient

    from app.main import create_app

    c = TestClient(create_app())
    a, b = store.players[0], store.players[1]
    r = c.post(
        "/api/trades/evaluate",
        json={"team_a": "SEA", "team_b": "NYY", "team_a_receives": [a["id"]], "team_b_receives": [b["id"]]},
    )
    assert r.status_code == 200 and r.json()["narrative_source"] == "rules"
    n = c.post("/api/players/search/natural", json={"query": "lefty reliever"}).json()
    assert n["interpreted_by"] == "rules"


def test_rate_limit(store, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("AI_RATE_LIMIT_PER_MINUTE", "2")

    async def none(*a, **k):
        return None

    monkeypatch.setattr(llm, "parse_search", none)
    from fastapi.testclient import TestClient

    from app.main import create_app

    c = TestClient(create_app())
    codes = [c.post("/api/players/search/natural", json={"query": "lefty"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_cors_is_restricted(client):
    r = client.options(
        "/api/health", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"}
    )
    assert r.headers.get("access-control-allow-origin") != "*"
