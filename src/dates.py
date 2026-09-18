"""Date-wise card files: card_YYYY-MM-DD.json under data/."""

from __future__ import annotations

import json
import re
from pathlib import Path

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CARD_NAME = re.compile(r"^card_(\d{4}-\d{2}-\d{2})\.json$")


def is_iso_date(value: str | None) -> bool:
    return bool(value and ISO_DATE.fullmatch(value))


def card_path(data_dir: Path, iso_date: str) -> Path:
    return Path(data_dir) / f"card_{iso_date}.json"


def list_card_dates(data_dir: Path) -> list[str]:
    dates = []
    for path in Path(data_dir).glob("card_*.json"):
        match = CARD_NAME.match(path.name)
        if match:
            dates.append(match.group(1))
    return sorted(dates)


def summarise_cards(data_dir: Path) -> list[dict]:
    rows = []
    for iso in list_card_dates(data_dir):
        path = card_path(data_dir, iso)
        try:
            card = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        best = card.get("best_bet") or {}
        rows.append(
            {
                "date": iso,
                "href": f"day/{iso}/",
                "meetings": len(card.get("meetings") or []),
                "plays": len(card.get("plays") or []),
                "best_bet": {
                    "name": best.get("name"),
                    "venue": best.get("venue"),
                    "race_number": best.get("race_number"),
                    "odds": best.get("odds"),
                    "figure": best.get("figure"),
                }
                if best.get("name")
                else None,
            }
        )
    return rows
