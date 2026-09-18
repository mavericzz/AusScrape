"""Local AU handicapper desk."""

from __future__ import annotations

import json
import threading
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.dates import card_path, is_iso_date, list_card_dates, summarise_cards
from src.handicap.money import attach_card_money

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
FRONTEND = ROOT / "frontend"

app = FastAPI(title="AU Race Desk")
_scrape_lock = threading.Lock()
_scrape_status = {"running": False, "log": []}


def default_card_date() -> str:
    return date.today().isoformat()


if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")


@app.get("/styles.css")
def styles():
    return FileResponse(FRONTEND / "styles.css", media_type="text/css")


@app.get("/app.js")
def app_js():
    return FileResponse(FRONTEND / "app.js", media_type="text/javascript")


@app.get("/index.js")
def index_js():
    return FileResponse(FRONTEND / "index.js", media_type="text/javascript")


@app.get("/site.js")
def site_js():
    return FileResponse(FRONTEND / "site.js", media_type="text/javascript")


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "frontend missing")
    return FileResponse(index_path)


@app.get("/day/{iso_date}")
def day_page(iso_date: str):
    if not is_iso_date(iso_date):
        raise HTTPException(404, "not a date")
    desk = FRONTEND / "desk.html"
    if not desk.exists():
        raise HTTPException(404, "desk missing")
    return FileResponse(desk)


@app.get("/api/dates")
def dates():
    return {"dates": summarise_cards(DATA), "available": list_card_dates(DATA)}


@app.get("/api/card")
def card(date: str | None = None):
    iso = date if is_iso_date(date) else None
    path = card_path(DATA, iso) if iso else None
    if path is None or not path.exists():
        latest = list_card_dates(DATA)
        path = card_path(DATA, latest[-1]) if latest else None
    if path is None or not path.exists():
        return {"date": iso or "", "meetings": [], "plays": [], "empty": True}
    return attach_card_money(json.loads(path.read_text()))


@app.get("/api/status")
def status():
    return _scrape_status


@app.post("/api/scrape")
def scrape(date: str | None = None, jev: bool = False):
    iso = date if is_iso_date(date) else default_card_date()
    if not _scrape_lock.acquire(blocking=False):
        return {"ok": False, "error": "scrape already running"}

    def run():
        _scrape_status["running"] = True
        _scrape_status["log"] = [f"Scraping {iso}"]
        try:
            import subprocess
            import sys

            cmd = [sys.executable, str(ROOT / "scripts" / "scrape_au.py"), "--date", iso]
            if jev:
                cmd.append("--jev")
            proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=3600)
            _scrape_status["log"] = (proc.stdout or proc.stderr or "").splitlines()[-80:]
            _scrape_status["code"] = proc.returncode
        except Exception as exc:
            _scrape_status["log"].append(str(exc))
        finally:
            _scrape_status["running"] = False
            _scrape_lock.release()

    threading.Thread(target=run, daemon=True).start()
    return {"ok": True, "date": iso}
