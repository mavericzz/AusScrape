"""Read thoroughbred/FormRace racecard snapshots when present."""

from __future__ import annotations

import json
from pathlib import Path

from src.parse import horse_key


def default_root() -> Path:
    return Path("/Users/toshasharma/Downloads/Github/thoroughbred")


def load_tipster_card(iso_date: str, root: Path | None = None) -> dict | None:
    base = Path(root) if root else default_root()
    path = base / "outputs" / "tips" / iso_date / "card.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def odds_by_horse(card: dict | None) -> dict[str, float]:
    out: dict[str, float] = {}
    if not card:
        return out
    for meeting in card.get("meetings") or []:
        for race in meeting.get("races") or []:
            for runner in race.get("field") or race.get("runners") or []:
                name = runner.get("horse") or runner.get("name")
                odds = runner.get("odds") or runner.get("win_odds")
                if not name or not odds:
                    continue
                try:
                    out[horse_key(name)] = float(odds)
                except (TypeError, ValueError):
                    continue
    return out


def apply_thoroughbred_odds(racing: dict, card: dict | None) -> dict:
    odds = odds_by_horse(card)
    if not odds:
        return racing
    meetings = []
    for meeting in racing.get("meetings") or []:
        races = []
        for race in meeting.get("races") or []:
            runners = []
            for runner in race.get("runners") or []:
                key = horse_key(runner.get("name") or "")
                if key in odds and not runner.get("odds"):
                    runners.append({**runner, "odds": odds[key], "odds_source": "thoroughbred"})
                else:
                    runners.append(runner)
            races.append({**race, "runners": runners})
        meetings.append({**meeting, "races": races})
    return {**racing, "meetings": meetings}
