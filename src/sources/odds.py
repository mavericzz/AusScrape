"""Market odds from TheRacingAPI racecards, matched by horse name."""

from __future__ import annotations

import os
import time

import httpx

from src.parse import horse_key

BASE_URL = "https://api.theracingapi.com/v1"


def _as_odds(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value) if float(value) > 1 else None
    if isinstance(value, list):
        prices = [_as_odds(item if not isinstance(item, dict) else item.get("win_odds") or item.get("odds")) for item in value]
        prices = [p for p in prices if p]
        return min(prices) if prices else None
    if isinstance(value, dict):
        return _as_odds(value.get("win_odds") or value.get("odds") or value.get("win"))
    try:
        parsed = float(str(value).replace("$", "").strip())
    except ValueError:
        return None
    return parsed if parsed > 1 else None


def _runner_name(runner: dict) -> str:
    horses = runner.get("horses") if isinstance(runner.get("horses"), dict) else {}
    return runner.get("horse") or runner.get("horse_name") or runner.get("name") or horses.get("name") or ""


def _runner_odds(runner: dict) -> float | None:
    for key in ("current_odds", "win_odds", "odds", "sp"):
        parsed = _as_odds(runner.get(key))
        if parsed:
            return parsed
    return None


def odds_from_race(payload: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    runners = payload.get("runners") or payload.get("horses") or []
    if isinstance(payload.get("races"), list):
        for race in payload["races"]:
            out.update(odds_from_race(race))
        return out
    for runner in runners:
        name = _runner_name(runner)
        price = _runner_odds(runner)
        if name and price:
            out[horse_key(name)] = price
    return out


def apply_market_odds(racing: dict, odds: dict[str, float]) -> dict:
    meetings = []
    for meeting in racing.get("meetings") or []:
        races = []
        for race in meeting.get("races") or []:
            runners = []
            for runner in race.get("runners") or []:
                key = horse_key(runner.get("name") or "")
                if runner.get("odds") in (None, "", 0) and key in odds:
                    runners.append({**runner, "odds": odds[key], "odds_source": "theracingapi"})
                else:
                    runners.append(runner)
            races.append({**race, "runners": runners})
        meetings.append({**meeting, "races": races})
    return {**racing, "meetings": meetings}


def fetch_day_odds(iso_date: str, username: str | None = None, password: str | None = None) -> dict[str, float]:
    user = username or os.environ.get("RACING_API_USER")
    password = password or os.environ.get("RACING_API_PASS")
    if not user or not password:
        return {}
    mapped: dict[str, float] = {}
    with httpx.Client(timeout=30.0, auth=(user, password)) as client:
        meets = client.get(f"{BASE_URL}/australia/meets", params={"date": iso_date})
        meets.raise_for_status()
        body = meets.json()
        meet_list = body.get("meets") or body.get("meetings") or body if isinstance(body, list) else []
        for meet in meet_list:
            meet_id = meet.get("meet_id") or meet.get("id")
            if not meet_id:
                continue
            time.sleep(0.55)
            races = client.get(f"{BASE_URL}/australia/meets/{meet_id}/races")
            if races.status_code >= 400:
                continue
            payload = races.json()
            race_list = payload.get("races") or payload if isinstance(payload, list) else []
            mapped.update(odds_from_race({"races": race_list} if isinstance(race_list, list) else payload))
            for race in race_list if isinstance(race_list, list) else []:
                number = race.get("race_number") or race.get("number")
                if not number:
                    mapped.update(odds_from_race(race))
                    continue
                time.sleep(0.55)
                detail = client.get(f"{BASE_URL}/australia/meets/{meet_id}/races/{number}")
                if detail.status_code < 400:
                    mapped.update(odds_from_race(detail.json()))
    return mapped
