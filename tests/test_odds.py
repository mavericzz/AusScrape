from src.sources.odds import apply_market_odds, odds_from_race


def test_odds_from_race_reads_nested_names_and_book_list():
    payload = {
        "runners": [
            {"horses": {"name": "Sprint King"}, "odds": [{"win_odds": "4.80"}, {"win_odds": "5.00"}]},
            {"horse_name": "Slow Closer", "current_odds": "3.20"},
        ]
    }
    mapped = odds_from_race(payload)
    assert mapped["sprintking"] == 4.8
    assert mapped["slowcloser"] == 3.2


def test_apply_market_odds_fills_missing_prices_only():
    racing = {
        "meetings": [
            {
                "races": [
                    {
                        "runners": [
                            {"name": "Sprint King", "odds": None},
                            {"name": "Priced", "odds": 9.0},
                        ]
                    }
                ]
            }
        ]
    }
    out = apply_market_odds(racing, {"sprintking": 4.8, "priced": 2.1})
    runners = out["meetings"][0]["races"][0]["runners"]
    assert runners[0]["odds"] == 4.8
    assert runners[1]["odds"] == 9.0
