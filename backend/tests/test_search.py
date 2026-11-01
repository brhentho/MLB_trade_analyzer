from app import search
from app.schemas import SearchFilters


def _p(**kw):
    base = {
        "id": 1,
        "name": "Test Player",
        "team": "SEA",
        "team_id": 136,
        "group": "pitcher",
        "position": "P",
        "role": "RP",
        "bats": "L",
        "throws": "L",
        "age": 27,
        "war": 1.2,
        "surplus": 10.0,
        "ovr": 55,
        "pot": 55,
        "ratings": {"stuff": 66, "contact_mgmt": 55, "control": 50, "velocity": 60, "stamina": 30},
        "percentiles": {"chase_percent": 94.0},
        "contract": {"salary_now": 4.1, "control_through": 2029, "verified": False, "status": "arbitration"},
        "archetypes": ["strikeout-artist"],
        "proj_war": [1.0],
    }
    base.update(kw)
    return base


def test_filters_match_and_explain():
    f = SearchFilters(
        group="pitcher",
        roles=["RP"],
        throws=["L"],
        percentiles_min={"chase_percent": 90},
        salary_max=6,
        control_min_years=2,
    )
    reasons = search.evaluate(_p(), f, 2027)
    labels = [r["label"] for r in reasons]
    assert "Chase% 94th pct" in labels
    assert "$4.1M in 2027" in labels
    assert "3 yrs control" in labels


def test_filters_reject():
    assert search.evaluate(_p(), SearchFilters(salary_max=3), 2027) is None
    assert search.evaluate(_p(), SearchFilters(throws=["R"]), 2027) is None
    assert search.evaluate(_p(), SearchFilters(control_min_years=4), 2027) is None
    assert search.evaluate(_p(), SearchFilters(ratings_min={"control": 60}), 2027) is None


def test_outfield_alias():
    hitter = _p(group="hitter", position="CF", role="CF", ratings={})
    assert search.evaluate(hitter, SearchFilters(positions=["OF"]), 2027) is not None
    assert search.evaluate(hitter, SearchFilters(positions=["IF"]), 2027) is None


def test_parse_query_reliever():
    f, _ = search.parse_query("left-handed reliever with elite chase rate under $6M, 2+ years of control")
    assert f.group == "pitcher" and f.roles == ["RP"] and f.throws == ["L"]
    assert f.salary_max == 6 and f.control_min_years == 2
    assert f.percentiles_min == {"chase_percent": 90}
    assert f.ratings_min is None


def test_parse_query_command_is_skill():
    f, _ = search.parse_query("starter with plus control")
    assert f.roles == ["SP"] and f.ratings_min == {"control": 60}


def test_parse_query_hitter():
    f, notes = search.parse_query("young power hitting shortstop with speed")
    assert f.positions == ["SS"] and f.group == "hitter"
    assert f.ratings_min["power"] == 60 and f.ratings_min["speed"] == 62
    assert f.age_max == 26 and notes


def test_parse_query_empty():
    f, notes = search.parse_query("hello there")
    assert f.model_dump(exclude_defaults=True) == {}
    assert notes


def test_similar_respects_role_and_budget():
    target = _p(id=1)
    pool = [
        target,
        _p(id=2, contract={**target["contract"], "salary_now": 1.0}),
        _p(id=3, role="SP"),
        _p(id=4, contract={**target["contract"], "salary_now": 20.0}),
    ]
    res = search.similar(target, pool, 10, 2027, salary_max=5)
    assert [r["player"]["id"] for r in res] == [2]
    assert res[0]["similarity"] == 100.0
