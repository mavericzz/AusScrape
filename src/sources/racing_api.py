"""TheRacingAPI AU racecards — primary Sunday fields and market odds."""

from __future__ import annotations

import os
import time

import httpx

from src.parse import parse_distance_m, parse_weight
from src.sources.odds import _runner_odds

BASE_URL = "https://api.theracingapi.com/v1"


def last_finish_from_form(form: str | None) -> int | None:
    if not form:
        return None
    for char in reversed(str(form).replace("x", "-").replace("X", "-")):
        if char.isdigit():
            return 10 if char == "0" else int(char)
        if char not in "-/":
            break
    return None


def _intish(value) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def meetings_from_api(payload: dict, iso_date: str) -> dict:
    meetings = []
    for meet in payload.get("meets") or payload.get("meetings") or []:
        races = []
        for race in meet.get("races") or []:
            if race.get("is_trial") or race.get("is_jump_out"):
                continue
            runners = []
            for runner in race.get("runners") or []:
                if runner.get("scratched"):
                    continue
                finish = last_finish_from_form(runner.get("form"))
                runners.append(
                    {
                        "name": runner.get("horse") or "",
                        "number": _intish(runner.get("number")),
                        "barrier": _intish(runner.get("draw")),
                        "weight_kg": parse_weight(runner.get("weight")),
                        "jockey": runner.get("jockey") or "",
                        "trainer": runner.get("trainer") or "",
                        "handicap_rating": _intish(runner.get("rating")) if not isinstance(runner.get("rating"), dict) else None,
                        "odds": _runner_odds(runner),
                        "form_string": runner.get("form"),
                        "comments": runner.get("comment") or None,
                        "last_run": {"finish": finish, "beaten_lengths": 0.0 if finish == 1 else None},
                        "scratched": False,
                    }
                )
            races.append(
                {
                    "race_number": _intish(race.get("race_number")) or 0,
                    "name": race.get("race_name") or f"Race {race.get('race_number')}",
                    "distance_m": parse_distance_m(race.get("distance")),
                    "going": race.get("going"),
                    "off_time": race.get("off_time"),
                    "runners": runners,
                }
            )
        if not any(race["runners"] for race in races):
            continue
        venue = meet.get("course") or meet.get("venue") or ""
        meetings.append(
            {
                "meet_code": meet.get("meet_id") or meet.get("id"),
                "venue": venue,
                "state": meet.get("state"),
                "date": iso_date,
                "races": races,
            }
        )
    by_venue: dict[str, dict] = {}
    for meeting in meetings:
        key = (meeting.get("venue") or "").lower()
        prev = by_venue.get(key)
        n = sum(len(r.get("runners") or []) for r in meeting.get("races") or [])
        p = sum(len(r.get("runners") or []) for r in (prev.get("races") if prev else []) or [])
        if prev is None or n > p:
            by_venue[key] = meeting
    return {"date": iso_date, "source": "theracingapi", "meetings": list(by_venue.values())}


def fetch_day_card(iso_date: str, username: str | None = None, password: str | None = None) -> dict:
    user = username or os.environ.get("RACING_API_USER")
    password = password or os.environ.get("RACING_API_PASS")
    if not user or not password:
        return {"date": iso_date, "source": "theracingapi", "meetings": []}
    with httpx.Client(timeout=30.0, auth=(user, password)) as client:
        meets = client.get(f"{BASE_URL}/australia/meets", params={"date": iso_date})
        meets.raise_for_status()
        payload = meets.json()
        meet_list = payload.get("meets") or []
        filled = []
        for meet in meet_list:
            meet_id = meet.get("meet_id") or meet.get("id")
            time.sleep(0.55)
            races = client.get(f"{BASE_URL}/australia/meets/{meet_id}/races")
            if races.status_code >= 400:
                filled.append(meet)
                continue
            body = races.json()
            filled.append({**meet, "races": body.get("races") or []})
        return meetings_from_api({"meets": filled}, iso_date)
