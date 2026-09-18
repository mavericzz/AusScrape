from src.sources.merge import attach_sectionals, merge_and_score


def test_attach_sectionals_uses_most_recent_run_for_the_horse():
    racing = {
        "meetings": [
            {
                "venue": "Nowra",
                "races": [
                    {
                        "race_number": 1,
                        "runners": [{"name": "Don's Party", "number": 4}],
                    }
                ],
            }
        ]
    }
    sectionals = {
        "meetings": [
            {
                "venue": "Newcastle",
                "races": [
                    {
                        "sectionals": [
                            {"horse_name": "Don's Party", "meeting_date": "2026-08-11", "l400_split": 11.48, "late_speed": 61.02, "early_speed": 57.07, "track_condition": "Soft"},
                            {"horse_name": "Don's Party", "meeting_date": "2026-08-30", "l400_split": 12.48, "late_speed": 58.44, "early_speed": 58.05, "track_condition": "Good"},
                        ]
                    }
                ],
            }
        ]
    }
    out = attach_sectionals(racing, sectionals)
    horse = out["meetings"][0]["races"][0]["runners"][0]
    assert horse["sectionals"]["meeting_date"] == "2026-08-30"
    assert horse["sectionals"]["l400_split"] == 12.48


def test_merge_and_score_emits_plays_and_a_best_bet():
    racing = {
        "date": "2026-09-20",
        "meetings": [
            {
                "venue": "Armidale",
                "going": "Soft",
                "races": [
                    {
                        "race_number": 7,
                        "name": "BM66",
                        "distance_m": 1100,
                        "going": "Soft",
                        "runners": [
                            {
                                "name": "Sprint King",
                                "number": 2,
                                "barrier": 3,
                                "weight_kg": 56.0,
                                "handicap_rating": 66,
                                "odds": 4.8,
                                "scratched": False,
                                "last_run": {"finish": 1, "beaten_lengths": 0, "distance_m": 1100, "weight_kg": 58, "going": "Soft"},
                                "sectionals": {"l400_split": 11.1, "late_speed": 62.0, "early_speed": 59.0, "track_condition": "Soft"},
                            },
                            {
                                "name": "Slow Closer",
                                "number": 8,
                                "barrier": 10,
                                "weight_kg": 58.5,
                                "handicap_rating": 64,
                                "odds": 3.2,
                                "scratched": False,
                                "last_run": {"finish": 6, "beaten_lengths": 6.5, "distance_m": 1400, "weight_kg": 55, "going": "Good"},
                            },
                        ],
                    }
                ],
            }
        ],
    }
    card = merge_and_score(racing, extra_sources=[])
    assert card["date"] == "2026-09-20"
    assert card["best_bet"]["name"]
    assert card["meetings"][0]["races"][0]["runners"][0]["rank"] == 1
    money = {row["name"]: row["money_bet"] for row in card["meetings"][0]["races"][0]["runners"]}
    assert money["Sprint King"] > 0
    assert money["Slow Closer"] > money["Sprint King"]
