"""Day-wide best bet from overlay plays, else strongest rank-1."""

from __future__ import annotations


def pick_best_bet(card: dict) -> dict | None:
    plays = list(card.get("plays") or [])
    if plays:
        best = max(plays, key=lambda p: (p.get("edge") or 0, p.get("figure") or 0, p.get("p_model") or 0))
        return {**best, "label": "BEST BET OF THE DAY"}

    candidates: list[dict] = []
    for meeting in card.get("meetings") or []:
        for race in meeting.get("races") or []:
            for runner in race.get("runners") or []:
                if runner.get("rank") != 1:
                    continue
                candidates.append(
                    {
                        **runner,
                        "venue": meeting.get("venue"),
                        "race_number": race.get("race_number"),
                        "race_name": race.get("name"),
                    }
                )
    if not candidates:
        return None
    best = max(candidates, key=lambda p: (p.get("figure") or 0, p.get("p_model") or 0))
    return {**best, "label": "BEST BET OF THE DAY"}
