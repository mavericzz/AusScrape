"""Name keys and racing.com unit parsers."""

from __future__ import annotations

import re

VENUE_PREFIXES = ("bet365", "ladbrokes", "sportsbet", "aquispark")


def horse_key(name: str) -> str:
    stripped = re.sub(r"\([^)]*\)", "", name or "")
    return re.sub(r"[^a-z0-9]+", "", stripped.lower())


def venue_key(name: str) -> str:
    key = horse_key(name or "")
    for prefix in VENUE_PREFIXES:
        if key.startswith(prefix):
            key = key[len(prefix) :]
            break
    return key


def parse_weight(text: str | None) -> float | None:
    if text is None or text == "":
        return None
    cleaned = str(text).replace("kg", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_margin(margin: str | None) -> float | None:
    if not margin:
        return None
    cleaned = str(margin).replace("L", "").replace("l", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_sp(sp: str | None) -> float | None:
    if not sp:
        return None
    cleaned = str(sp).replace("$", "").strip()
    try:
        val = float(cleaned)
    except ValueError:
        return None
    return val if val > 0 else None


def parse_distance_m(dist: str | None) -> int | None:
    if not dist:
        return None
    cleaned = re.sub(r"[^0-9]", "", str(dist))
    return int(cleaned) if cleaned else None
