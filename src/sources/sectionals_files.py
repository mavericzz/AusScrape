"""Load Punters sectional JSON from sectionalscarper."""

from __future__ import annotations

import json
from pathlib import Path


def default_root() -> Path:
    return Path("/Users/toshasharma/Downloads/Github/sectionalscarper")


def load_recent_sectionals(root: Path | None = None, limit: int = 14) -> dict:
    base = Path(root) if root else default_root()
    files = sorted((base / "data").glob("sectionals_*.json"))[-limit:]
    meetings: list[dict] = []
    for path in files:
        try:
            blob = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        meetings.extend(blob.get("meetings") or [])
    return {"meetings": meetings}
