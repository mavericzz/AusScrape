from src.sources.racing_com import last_flat_start, parse_entries, to_meeting


def test_parse_entries_keeps_flat_form_and_drops_trials():
    entries = [
        {
            "horseName": "Nicish",
            "raceEntryNumber": 3,
            "barrierNumber": 5,
            "weight": "54kg",
            "jockeyName": "J. Holder",
            "trainerName": "R. Balfour",
            "handicapRating": 62,
            "scratched": False,
            "horse": {
                "careerStats": "18-3-2-1",
                "lastTen": ["3", "1", "5", "2", "8"],
                "horseForm": [
                    {
                        "date": "2026-09-06",
                        "venue": "Morphettville Parks",
                        "distance": "1400m",
                        "raceClass": "BM64",
                        "trackCondition": "Good 4",
                        "weightCarried": "55kg",
                        "position": 1,
                        "margin": "0.8L",
                        "startingPrice": "$$6.50",
                        "isTrial": False,
                        "commentStewards": "Led. Kicked clear.",
                        "commentBestBets": "Won well.",
                    },
                    {
                        "date": "2026-08-20",
                        "venue": "Morphettville",
                        "distance": "1000m",
                        "raceClass": "3YO-BT",
                        "trackCondition": "Soft",
                        "position": 2,
                        "startingPrice": None,
                        "isTrial": False,
                    },
                ],
            },
        }
    ]
    runners = parse_entries(entries)
    assert len(runners) == 1
    horse = runners[0]
    assert horse["name"] == "Nicish"
    assert horse["career"]["career_wins"] == 3
    assert horse["form_string"] == "31528"
    assert len(horse["form_starts"]) == 1
    last = last_flat_start(horse)
    assert last["finish"] == 1
    assert last["track"] == "Morphettville Parks"
    assert "Led" in (horse["comments"] or "")


def test_to_meeting_skips_scratched_from_the_live_field():
    raw = {
        "id": "5194194",
        "venueName": "nowra",
        "races": [
            {
                "raceNumber": 1,
                "raceEntries": [
                    {"horseName": "Live", "raceEntryNumber": 1, "scratched": False, "horse": {}},
                    {"horseName": "Out", "raceEntryNumber": 2, "scratched": True, "horse": {}},
                ],
            }
        ],
    }
    meeting = to_meeting(raw, "2026-09-20")
    names = [r["name"] for r in meeting["races"][0]["runners"]]
    assert names == ["Live"]
