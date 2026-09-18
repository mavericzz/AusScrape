from src.handicap.money import attach_card_money, attach_race_money, market_shares


def test_market_shares_split_the_win_book_from_odds():
    shares = market_shares([2.0, 4.0, None])
    assert shares[0] == 2 / 3
    assert shares[1] == 1 / 3
    assert shares[2] is None


def test_attach_race_money_puts_dollars_and_percent_on_each_horse():
    race = attach_race_money(
        {
            "race_number": 1,
            "runners": [
                {"name": "Fav", "odds": 2.0},
                {"name": "Second", "odds": 4.0},
                {"name": "No price", "odds": None},
            ],
        }
    )
    fav, second, blank = race["runners"]
    assert fav["money_pct"] == 0.6667
    assert second["money_pct"] == 0.3333
    assert fav["money_bet"] == 6667
    assert second["money_bet"] == 3333
    assert blank["money_bet"] is None
    assert race["money_book"] == 10000


def test_attach_card_money_copies_onto_plays_and_best_bet():
    card = attach_card_money(
        {
            "meetings": [
                {
                    "venue": "Caulfield",
                    "races": [
                        {
                            "race_number": 1,
                            "runners": [
                                {"name": "Politely Dun", "odds": 12.0},
                                {"name": "Emperor Tzu", "odds": 5.5},
                            ],
                        }
                    ],
                }
            ],
            "plays": [{"name": "Politely Dun", "venue": "Caulfield", "race_number": 1}],
            "best_bet": {"name": "Politely Dun", "venue": "Caulfield", "race_number": 1},
        }
    )
    horse = card["meetings"][0]["races"][0]["runners"][0]
    assert horse["money_bet"] == card["plays"][0]["money_bet"]
    assert horse["money_bet"] == card["best_bet"]["money_bet"]
    assert horse["money_bet"] > 0
