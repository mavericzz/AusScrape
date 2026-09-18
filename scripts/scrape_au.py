"""Build Sunday AU desk card from racing.com, sectionals, thoroughbred, jev."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _load_env() -> None:
    load_dotenv(ROOT / ".env")
    tb = Path("/Users/toshasharma/Downloads/Github/thoroughbred/backend/.env")
    if tb.exists():
        load_dotenv(tb, override=False)


def default_date() -> str:
    today = date.today()
    # After 8pm local, still useful to build tomorrow; otherwise tomorrow.
    return (today + timedelta(days=1)).isoformat()


def build_card(iso_date: str, use_jev: bool = False) -> dict:
    from src.sources.jev import scrape_all
    from src.sources.merge import attach_sectionals, merge_and_score
    from src.sources.racing_api import fetch_day_card
    from src.sources.racing_com import fetch_day
    from src.sources.sectionals_files import load_recent_sectionals
    from src.sources.thoroughbred import apply_thoroughbred_odds, load_tipster_card

    racing = fetch_day_card(iso_date)
    if not any(race.get("runners") for meeting in racing.get("meetings") or [] for race in meeting.get("races") or []):
        racing = fetch_day(iso_date, tab_only=True)
    racing = attach_sectionals(racing, load_recent_sectionals())
    racing = apply_thoroughbred_odds(racing, load_tipster_card(iso_date))

    extras = []
    if use_jev:
        extras = scrape_all(iso_date)
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / f"jev_{iso_date}.json").write_text(json.dumps(extras, indent=2))

    card = merge_and_score(racing, extra_sources=extras)
    card["jev"] = [
        {"source": e.get("source"), "ok": e.get("ok"), "url": e.get("url"), "error": e.get("error")}
        for e in extras
    ]
    return card


def write_card(card: dict) -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    iso = card.get("date") or "card"
    path = DATA / f"card_{iso}.json"
    path.write_text(json.dumps(card, indent=2))
    return path


def main() -> None:
    _load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=default_date())
    parser.add_argument("--jev", action="store_true", help="Run jev-ultrafast browser scrapes")
    args = parser.parse_args()
    print(f"Building AU desk for {args.date} jev={args.jev}", flush=True)
    card = build_card(args.date, use_jev=args.jev)
    path = write_card(card)
    best = card.get("best_bet") or {}
    n_meet = len(card.get("meetings") or [])
    n_play = len(card.get("plays") or [])
    print(f"Wrote {path} meetings={n_meet} plays={n_play} best={best.get('name')} {best.get('venue')} R{best.get('race_number')}")


if __name__ == "__main__":
    main()
