from src.parse import parse_weight
from src.sources.racing_api import meetings_from_api


def test_meetings_from_api_maps_fields_odds_and_last_form_figure():
    payload = {
        "meets": [
            {
                "course": "Bendigo",
                "state": "VIC",
                "meet_id": "m1",
                "races": [
                    {
                        "race_number": 3,
                        "race_name": "BM64",
                        "distance": "1400",
                        "going": "Soft",
                        "off_time": "14:30",
                        "is_trial": False,
                        "runners": [
                            {
                                "horse": "Sprint King",
                                "number": "2",
                                "draw": "3",
                                "weight": "56kg",
                                "odds": [{"bookmaker": "Sportsbet", "win_odds": "4.80"}],
                                "comment": "Led. Kicked clear.",
                                "form": "x3121",
                                "scratched": False,
                                "jockey": "B. Shinn",
                                "trainer": "G. Waterhouse",
                            },
                            {
                                "horse": "Out",
                                "number": "9",
                                "scratched": True,
                            },
                        ],
                    }
                ],
            },
            {
                "course": "Bendigo",
                "meet_id": "m1-empty",
                "races": [{"race_number": 1, "runners": []}],
            },
        ]
    }
    card = meetings_from_api(payload, "2026-09-20")
    assert len(card["meetings"]) == 1
    meeting = card["meetings"][0]
    assert meeting["venue"] == "Bendigo"
    race = meeting["races"][0]
    assert race["distance_m"] == 1400
    assert len(race["runners"]) == 1
    horse = race["runners"][0]
    assert horse["odds"] == 4.8
    assert horse["weight_kg"] == 56.0
    assert horse["last_run"]["finish"] == 1
    assert "Led" in horse["comments"]
