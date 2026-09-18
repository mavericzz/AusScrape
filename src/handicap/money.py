"""Win-market money on each horse from current odds."""

from __future__ import annotations

from src.parse import horse_key

DEFAULT_BOOK = 10000.0


def market_shares(odds_list: list[float | None]) -> list[float | None]:
    weights: list[float | None] = []
    for odds in odds_list:
        try:
            price = float(odds) if odds not in (None, "", 0) else None
        except (TypeError, ValueError):
            price = None
        weights.append(1.0 / price if price and price > 1 else None)
    total = sum(weight for weight in weights if weight)
    if not total:
        return [None] * len(odds_list)
    return [None if weight is None else weight / total for weight in weights]


def attach_race_money(race: dict, book: float = DEFAULT_BOOK) -> dict:
    runners = list(race.get("runners") or [])
    shares = market_shares([runner.get("odds") for runner in runners])
    out = []
    for runner, share in zip(runners, shares):
        row = dict(runner)
        row["money_pct"] = round(share, 4) if share is not None else None
        row["money_bet"] = round(share * book) if share is not None else None
        out.append(row)
    return {**race, "runners": out, "money_book": book}


def _runner_key(venue, race_number, name) -> tuple:
    return (venue or "", race_number, horse_key(name or ""))


def attach_card_money(card: dict, book: float = DEFAULT_BOOK) -> dict:
    index: dict[tuple, dict] = {}
    meetings = []
    for meeting in card.get("meetings") or []:
        venue = meeting.get("venue")
        races = []
        for race in meeting.get("races") or []:
            filled = attach_race_money(race, book=book)
            races.append(filled)
            for runner in filled.get("runners") or []:
                index[_runner_key(venue, race.get("race_number"), runner.get("name"))] = runner
        meetings.append({**meeting, "races": races})

    def with_money(row: dict | None) -> dict | None:
        if not row:
            return row
        src = index.get(_runner_key(row.get("venue"), row.get("race_number"), row.get("name")))
        if not src:
            return dict(row)
        return {**row, "money_pct": src.get("money_pct"), "money_bet": src.get("money_bet")}

    return {
        **card,
        "meetings": meetings,
        "plays": [with_money(play) for play in card.get("plays") or []],
        "best_bet": with_money(card.get("best_bet")),
        "money_book": book,
    }
