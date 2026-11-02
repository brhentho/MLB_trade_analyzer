import pytest

from app import model


@pytest.mark.parametrize("pct,expected", [(50, 50), (84, 60), (16, 40), (98, 71), (2, 29), (100, 76), (0, 24)])
def test_percentile_to_scout(pct, expected):
    assert model.percentile_to_scout(pct) == expected


def test_percentile_to_scout_none():
    assert model.percentile_to_scout(None) is None


def test_ratings_ignore_missing_inputs():
    r = model.ratings_from_percentiles(
        {"k_percent": 84, "whiff_percent": None},
        {"contact": ("k_percent", "whiff_percent"), "speed": ("sprint_speed",)},
    )
    assert r == {"contact": 60, "speed": None}


def test_innings_notation():
    assert model.innings_to_float("10.1") == pytest.approx(10 + 1 / 3)
    assert model.innings_to_float("7.2") == pytest.approx(7 + 2 / 3)
    assert model.innings_to_float(None) == 0


def test_hitter_war_average_regular_is_about_two():
    war = model.hitter_war(0.316, 0.316, 650, "2B", 50)
    assert 1.8 <= war <= 2.6


def test_hitter_war_rewards_premium_position():
    assert model.hitter_war(0.33, 0.316, 600, "SS", None) > model.hitter_war(0.33, 0.316, 600, "1B", None)


def test_pitcher_war_league_average_starter():
    war = model.pitcher_war(4.05, 4.05, 180, True)
    assert 1.5 <= war <= 2.5
    assert model.pitcher_war(None, 4.0, 0, True) == 0.0


def test_projection_regresses_and_ages():
    young = model.project_war(4.0, 23, 3, False, 0.8)
    old = model.project_war(4.0, 34, 3, False, 0.8)
    assert young[0] > old[0]
    assert old[2] < old[0]


def test_surplus_value():
    assert model.surplus_value([2.0], [10.0], 9.0) == 8.0
    assert model.surplus_value([1.0, 1.0], [0, 0], 10.0, inflation=0.1) == 21.0


def test_archetypes():
    r = {"power": 70, "eye": 60, "contact": 35, "speed": 40, "glove": 50, "arm": 50}
    tags = model.archetypes_for(r, "hitter", {})
    assert "three-true-outcomes" in tags and "slugger" in tags
    assert model.archetypes_for({"stamina": 70}, "pitcher", {"role": "RP"}) == []
    assert "workhorse" in model.archetypes_for({"stamina": 70}, "pitcher", {"role": "SP"})


def test_rating_distance_needs_three_shared():
    assert model.rating_distance({"a": 50, "b": 50}, {"a": 50, "b": 50}, ["a", "b"]) is None
    assert model.rating_distance({"a": 50, "b": 50, "c": 50}, {"a": 60, "b": 50, "c": 50}, "abc") == pytest.approx(
        (100 / 3) ** 0.5
    )
