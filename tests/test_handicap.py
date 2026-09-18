from src.handicap.model import PastRun, RunnerInput, handicap_race


def _runner(**kwargs):
    base = dict(
        name="Alpha",
        number=1,
        barrier=2,
        today_weight_kg=56.0,
        handicap_rating=68,
        market_odds=4.2,
        last_run=PastRun(finish=1, beaten_lengths=0.0, distance_m=1200, weight_kg=57.0, going="Soft"),
        going="Soft",
        distance_m=1200,
        field_size=8,
    )
    base.update(kwargs)
    return RunnerInput(**base)


def test_winner_dropping_weight_ranks_above_beaten_horse_at_shorter_odds():
    field = handicap_race(
        [
            _runner(name="Closer", last_run=PastRun(finish=1, beaten_lengths=0, distance_m=1200, weight_kg=58, going="Soft"), market_odds=5.0),
            _runner(name="Fav", last_run=PastRun(finish=4, beaten_lengths=4.5, distance_m=1200, weight_kg=55, going="Good"), market_odds=2.4, handicap_rating=70),
        ],
        venue="nowra",
    )
    names = [row["name"] for row in field]
    assert names[0] == "Closer"
    assert field[0]["rank"] == 1
    assert abs(sum(r["p_model"] for r in field) - 1.0) < 1e-6


def test_only_one_play_survives_in_a_race():
    field = handicap_race(
        [
            _runner(name="A", market_odds=4.0, handicap_rating=72, last_run=PastRun(finish=1, beaten_lengths=0, distance_m=1100, weight_kg=58, going="Soft")),
            _runner(name="B", market_odds=6.0, handicap_rating=71, last_run=PastRun(finish=1, beaten_lengths=0, distance_m=1100, weight_kg=57.5, going="Soft")),
        ],
        venue="armidale",
        min_edge=0.0,
    )
    plays = [r for r in field if r["action"] == "PLAY"]
    assert len(plays) <= 1
