"""racing.com public GraphQL form → AU desk meetings."""

from __future__ import annotations

import json
import re

import httpx

from src.parse import parse_distance_m, parse_margin, parse_sp, parse_weight

GQL_URL = "https://graphql.rmdprod.racing.com/"
GQL_KEY = "da2-6nsi4ztsynar3l3frgxf77q5fe"
_HEADERS = {"x-api-key": GQL_KEY, "Content-Type": "application/json"}
_AU_STATES = "VIC,NSW,QLD,SA,WA,TAS,ACT,NT"
_TRIAL_CODE_RE = re.compile(r"(?:^|[^A-Z])(?:BT|TRL|TRIAL|JUMP\s?OUT|JUMPOUT)(?:$|[^A-Z])")

_Q_MEETS = """query Meetings($daysBack:Int!,$daysForward:Int!,$states:String){
  GetRaceMeetingsByState(daysBack:$daysBack,daysForward:$daysForward,states:$states){
    id venueName date isTab isTrial country state
  }
}"""

_Q_RACE_FORM = """query RaceForm($meetCode:ID!,$raceNumber:Int!){
  getRaceForm(meetCode:$meetCode,raceNumber:$raceNumber){
    raceEntries{
      horseName raceEntryNumber barrierNumber weight jockeyName trainerName
      gearChanges gearHasChanges handicapRating scratched
      horse {
        name careerStats careerWins careerWinPercent careerPlacePercent lastTen
        horseForm {
          date venue distance raceClass trackCondition
          jockeyName weightCarried barrier starters
          position margin startingPrice prizeMoney
          winningTime commentStewards commentBestBets
          positionAt400 positionAt800
          isTrial isJumpOut horse1Name horse1Margin
        }
      }
    }
  }
}"""

_Q_MEETING_BY_DATE = """query MeetingByDate($date:String){
  GetMeetingByDate(date:$date){
    id venueName date state
    races {
      raceNumber
      raceEntries{
        horseName raceEntryNumber barrierNumber weight jockeyName trainerName
        gearChanges gearHasChanges handicapRating
        scratched
        horse {
          name
          careerStats careerWins careerWinPercent careerPlacePercent lastTen
          horseForm {
            date venue distance raceClass trackCondition
            jockeyName weightCarried barrier starters
            position margin startingPrice prizeMoney
            winningTime commentStewards commentBestBets
            positionAt400 positionAt800
            isTrial isJumpOut
            horse1Name horse1Margin
          }
        }
      }
    }
  }
}"""


def _post(query: str, variables: dict) -> dict | None:
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(GQL_URL, headers=_HEADERS, json={"query": query, "variables": variables})
            response.raise_for_status()
            body = response.json()
    except Exception:
        return None
    if body.get("errors") and not body.get("data"):
        return None
    return body.get("data")


def _is_trial(class_code: str | None, starting_price: object, flagged: bool) -> bool:
    if flagged:
        return True
    code = (class_code or "").upper()
    if "JUMPOUT" in code or "JUMP OUT" in code:
        return True
    if _TRIAL_CODE_RE.search(f" {code} "):
        return True
    return False


def parse_career_stats(horse: dict | None) -> dict:
    if not horse:
        return {}
    raw = (horse.get("careerStats") or "").strip()
    parts = raw.split("-")
    if len(parts) < 4:
        return {}
    try:
        starts, firsts, seconds, thirds = (int(p) for p in parts[:4])
    except (TypeError, ValueError):
        return {}
    if starts <= 0:
        return {}
    return {
        "career_starts": starts,
        "career_wins": firsts,
        "career_places": firsts + seconds + thirds,
        "career_win_rate": round(firsts / starts, 4),
    }


def parse_last_ten_form(horse: dict | None) -> str | None:
    if not horse:
        return None
    raw = horse.get("lastTen")
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return None
    if not isinstance(raw, list):
        return None
    figures = "".join(str(x) for x in raw if x is not None)
    return figures or None


def parse_horse_form(form_list: list[dict] | None) -> list[dict]:
    parsed = []
    for item in form_list or []:
        flagged = bool(item.get("isTrial") or item.get("isJumpOut"))
        if _is_trial(item.get("raceClass"), item.get("startingPrice"), flagged):
            continue
        position = item.get("position")
        margin = parse_margin(item.get("margin"))
        comments = " ".join(
            part for part in (item.get("commentStewards"), item.get("commentBestBets")) if part
        ).strip()
        parsed.append(
            {
                "race_date": item.get("date"),
                "track": item.get("venue"),
                "distance_m": parse_distance_m(item.get("distance")),
                "class_code": item.get("raceClass"),
                "going": item.get("trackCondition"),
                "weight_kg": parse_weight(item.get("weightCarried")),
                "finish": position,
                "beaten_lengths": 0.0 if position == 1 else margin,
                "starting_price": parse_sp(item.get("startingPrice")),
                "comments": comments or None,
            }
        )
    return parsed


def last_flat_start(runner: dict) -> dict | None:
    starts = runner.get("form_starts") or []
    return starts[0] if starts else None


def parse_entries(entries: list[dict] | None) -> list[dict]:
    runners = []
    for entry in entries or []:
        if entry.get("scratched"):
            continue
        horse = entry.get("horse") or {}
        form_starts = parse_horse_form(horse.get("horseForm") or [])
        comments = " ".join(
            start.get("comments") or "" for start in form_starts[:2] if start.get("comments")
        ).strip()
        last = form_starts[0] if form_starts else None
        runners.append(
            {
                "name": entry.get("horseName") or horse.get("name") or "",
                "number": entry.get("raceEntryNumber"),
                "barrier": entry.get("barrierNumber"),
                "weight_kg": parse_weight(entry.get("weight")),
                "jockey": entry.get("jockeyName") or "",
                "trainer": entry.get("trainerName") or "",
                "gear_changes": entry.get("gearChanges"),
                "handicap_rating": entry.get("handicapRating"),
                "scratched": False,
                "career": parse_career_stats(horse),
                "form_string": parse_last_ten_form(horse),
                "form_starts": form_starts,
                "last_run": last,
                "comments": comments or None,
                "last_sp": last.get("starting_price") if last else None,
            }
        )
    return runners


def to_meeting(raw: dict, target_date: str) -> dict:
    races = []
    for race in raw.get("races") or []:
        number = race.get("raceNumber")
        runners = parse_entries(race.get("raceEntries") or [])
        if not number:
            continue
        races.append(
            {
                "race_number": int(number),
                "name": race.get("raceName") or f"Race {number}",
                "distance_m": parse_distance_m(race.get("distance")),
                "going": race.get("trackCondition") or raw.get("trackCondition"),
                "runners": runners,
            }
        )
    venue = raw.get("venueName") or ""
    return {
        "meet_code": raw.get("id"),
        "venue": venue.replace("-", " ").title() if venue.islower() or "-" in venue else venue,
        "date": target_date,
        "races": races,
    }


def fetch_au_meetings(days_back: int = 0, days_forward: int = 2) -> list[dict]:
    all_meets: list[dict] = []
    for state in _AU_STATES.split(","):
        data = _post(_Q_MEETS, {"daysBack": days_back, "daysForward": days_forward, "states": state})
        if not data:
            continue
        for meet in data.get("GetRaceMeetingsByState") or []:
            if meet.get("country") == "Australia" and not meet.get("isTrial"):
                all_meets.append(meet)
    return all_meets


def fetch_race_form(meet_code: str, race_number: int) -> list[dict]:
    data = _post(_Q_RACE_FORM, {"meetCode": str(meet_code), "raceNumber": int(race_number)})
    if not data:
        return []
    form = data.get("getRaceForm") or {}
    return parse_entries(form.get("raceEntries") or [])


def fetch_meetings_by_date(target_date: str) -> list[dict]:
    data = _post(_Q_MEETING_BY_DATE, {"date": target_date})
    if not data:
        return []
    meetings_raw = data.get("GetMeetingByDate") or []
    if isinstance(meetings_raw, dict):
        meetings_raw = [meetings_raw]
    results = []
    for raw in meetings_raw:
        meeting = to_meeting(raw, target_date)
        meeting["state"] = raw.get("state")
        if meeting["races"]:
            results.append(meeting)
    return results


def fetch_day(target_date: str, tab_only: bool = True) -> dict:
    meetings = fetch_meetings_by_date(target_date)
    if meetings:
        return {"date": target_date, "source": "racing.com", "meetings": meetings}

    meetings_raw = [
        meet for meet in fetch_au_meetings(days_back=0, days_forward=2) if meet.get("date") == target_date
    ]
    if tab_only:
        meetings_raw = [meet for meet in meetings_raw if meet.get("isTab")]
    fallback = []
    for meet in meetings_raw:
        races = []
        for race_number in range(1, 13):
            runners = fetch_race_form(meet["id"], race_number)
            if not runners:
                if race_number == 1:
                    break
                continue
            races.append({"race_number": race_number, "name": f"Race {race_number}", "runners": runners})
        if not races:
            continue
        venue = meet.get("venueName") or ""
        fallback.append(
            {
                "meet_code": meet.get("id"),
                "venue": venue.replace("-", " ").title(),
                "state": meet.get("state"),
                "date": target_date,
                "races": races,
            }
        )
    return {"date": target_date, "source": "racing.com", "meetings": fallback}
