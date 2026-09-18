from src.handicap.best_bet import pick_best_bet


def test_best_bet_is_the_play_with_the_largest_edge():
    card = {
        "plays": [
            {"name": "Nicish", "venue": "Mount Gambier", "race_number": 9, "edge": 0.18, "figure": 71.2, "p_model": 0.19, "odds": 6.5, "action": "PLAY"},
            {"name": "Headwall", "venue": "Nowra", "race_number": 7, "edge": 0.31, "figure": 69.0, "p_model": 0.16, "odds": 8.0, "action": "PLAY"},
        ]
    }
    bet = pick_best_bet(card)
    assert bet["name"] == "Headwall"
    assert bet["label"] == "BEST BET OF THE DAY"


def test_best_bet_falls_back_to_strongest_rank_one_when_no_plays():
    card = {
        "plays": [],
        "meetings": [
            {
                "venue": "Kalgoorlie",
                "races": [
                    {
                        "race_number": 6,
                        "name": "Boulder Cup",
                        "runners": [
                            {"name": "Cup Horse", "rank": 1, "figure": 74.1, "odds": 4.6, "p_model": 0.22, "action": "WATCH"},
                            {"name": "Other", "rank": 2, "figure": 70.0, "odds": 7.0, "p_model": 0.11, "action": "PASS"},
                        ],
                    }
                ],
            }
        ],
    }
    bet = pick_best_bet(card)
    assert bet["name"] == "Cup Horse"
    assert bet["venue"] == "Kalgoorlie"
    assert bet["race_number"] == 6
