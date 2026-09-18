"""Join racing.com fields, Punters sectionals, and optional jev text, then score."""

from __future__ import annotations

from src.handicap.best_bet import pick_best_bet
from src.handicap.model import PastRun, RunnerInput, handicap_race
from src.handicap.money import attach_card_money
from src.parse import horse_key


def _index_sectionals(blob: dict) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for meeting in blob.get("meetings") or []:
        for race in meeting.get("races") or []:
            for row in race.get("sectionals") or []:
                key = horse_key(row.get("horse_name") or "")
                if not key:
                    continue
                prev = latest.get(key)
                date = row.get("meeting_date") or ""
                if prev is None or date >= (prev.get("meeting_date") or ""):
                    latest[key] = row
    return latest


def attach_sectionals(racing: dict, sectionals: dict) -> dict:
    index = _index_sectionals(sectionals)
    meetings = []
    for meeting in racing.get("meetings") or []:
        races = []
        for race in meeting.get("races") or []:
            runners = []
            for runner in race.get("runners") or []:
                sect = index.get(horse_key(runner.get("name") or ""))
                runners.append({**runner, "sectionals": sect} if sect else dict(runner))
            races.append({**race, "runners": runners})
        meetings.append({**meeting, "races": races})
    return {**racing, "meetings": meetings}


def _past_run(runner: dict) -> PastRun:
    last = dict(runner.get("last_run") or {})
    sect = runner.get("sectionals") or {}
    late = sect.get("late_speed")
    avg = sect.get("l400_speed") or sect.get("late_speed")
    return PastRun(
        finish=last.get("finish"),
        beaten_lengths=last.get("beaten_lengths"),
        distance_m=last.get("distance_m"),
        weight_kg=last.get("weight_kg"),
        going=last.get("going") or sect.get("track_condition"),
        class_code=last.get("class_code"),
        track=last.get("track"),
        fsp=float(late) if late not in (None, "") else None,
        par_fsp=float(avg) if avg not in (None, "") else None,
        l400_s=float(sect["l400_split"]) if sect.get("l400_split") not in (None, "") else None,
        early_speed=sect.get("early_speed") or last.get("early_speed"),
        late_speed=sect.get("late_speed") or last.get("late_speed"),
    )


def _apply_extra_text(runner: dict, extras: list[dict]) -> str | None:
    bits = [runner.get("comments") or ""]
    key = horse_key(runner.get("name") or "")
    for extra in extras:
        text = extra.get("text") or ""
        if key and key in horse_key(text):
            bits.append(text[:400])
        elif runner.get("name") and runner["name"] in text:
            bits.append(text[:400])
    joined = " ".join(bit for bit in bits if bit).strip()
    return joined or None


def merge_and_score(racing: dict, extra_sources: list[dict] | None = None) -> dict:
    extras = extra_sources or []
    meetings_out = []
    plays: list[dict] = []
    for meeting in racing.get("meetings") or []:
        venue = meeting.get("venue") or ""
        races_out = []
        for race in meeting.get("races") or []:
            runners = [r for r in (race.get("runners") or []) if not r.get("scratched")]
            going = race.get("going") or meeting.get("going")
            distance_m = race.get("distance_m") or 1200
            field_l400 = [
                float(r["sectionals"]["l400_split"])
                for r in runners
                if (r.get("sectionals") or {}).get("l400_split") not in (None, "")
            ]
            median_l400 = sorted(field_l400)[len(field_l400) // 2] if field_l400 else None
            inputs = []
            for runner in runners:
                past = _past_run(runner)
                past.field_l400_s = median_l400
                inputs.append(
                    RunnerInput(
                        name=runner.get("name") or "",
                        number=runner.get("number"),
                        barrier=runner.get("barrier"),
                        today_weight_kg=runner.get("weight_kg"),
                        handicap_rating=runner.get("handicap_rating"),
                        market_odds=runner.get("odds"),
                        last_run=past,
                        going=going,
                        distance_m=float(distance_m),
                        field_size=max(len(runners), 2),
                        rs_rating=runner.get("rs_rating"),
                        comments=_apply_extra_text(runner, extras),
                        scratched=bool(runner.get("scratched")),
                    )
                )
            scored = handicap_race(inputs, venue=venue)
            by_name = {row["name"]: row for row in scored}
            combined = []
            for runner in runners:
                row = {**runner, **(by_name.get(runner.get("name") or "") or {})}
                combined.append(row)
            combined.sort(key=lambda r: r.get("rank") or 99)
            race_plays = [r for r in combined if r.get("action") == "PLAY"]
            races_out.append(
                {
                    **race,
                    "going": going,
                    "distance_m": distance_m,
                    "plays": race_plays,
                    "runners": combined,
                }
            )
            for play in race_plays:
                plays.append(
                    {
                        **play,
                        "venue": venue,
                        "race_number": race.get("race_number"),
                        "race_name": race.get("name"),
                    }
                )
        meetings_out.append({**meeting, "races": races_out})
    card = {
        "date": racing.get("date"),
        "objective": "win overlay",
        "sources": ["racing.com", "sectionals", *[e.get("source") for e in extras if e.get("source")]],
        "meetings": meetings_out,
        "plays": plays,
    }
    card["best_bet"] = pick_best_bet(card)
    return attach_card_money(card)
