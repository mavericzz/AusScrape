"""Build a static AU desk for GitHub Pages."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from src.dates import card_path, list_card_dates, summarise_cards
from src.handicap.money import attach_card_money

FRONTEND_FILES = ("index.html", "index.js", "app.js", "site.js", "styles.css")
BASE_TAG = re.compile(r'<base href="[^"]*"\s*/?>')


def normalize_base(base_href: str) -> str:
    href = (base_href or "/").strip() or "/"
    if not href.startswith("/"):
        href = "/" + href
    if not href.endswith("/"):
        href += "/"
    return href


def rewrite_base(html: str, base_href: str) -> str:
    tag = f'<base href="{normalize_base(base_href)}" />'
    if BASE_TAG.search(html):
        return BASE_TAG.sub(tag, html, count=1)
    return html.replace("<head>", f"<head>\n  {tag}", 1)


def build_static_site(root: Path, dest: Path, base_href: str = "/") -> Path:
    root = Path(root)
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    frontend = root / "frontend"
    data_dir = root / "data"
    base = normalize_base(base_href)

    for name in FRONTEND_FILES:
        src = frontend / name
        if not src.exists():
            continue
        if name.endswith(".html"):
            (dest / name).write_text(rewrite_base(src.read_text(), base))
        else:
            shutil.copyfile(src, dest / name)

    desk_src = frontend / "desk.html"
    desk_html = rewrite_base(desk_src.read_text(), base) if desk_src.exists() else ""
    if desk_html:
        (dest / "desk.html").write_text(desk_html)

    dates = list_card_dates(data_dir)
    data_out = dest / "data"
    data_out.mkdir(parents=True)
    for iso in dates:
        card = json.loads(card_path(data_dir, iso).read_text())
        enriched = attach_card_money(card)
        (data_out / f"card_{iso}.json").write_text(json.dumps(enriched))
        if desk_html:
            day_dir = dest / "day" / iso
            day_dir.mkdir(parents=True)
            (day_dir / "index.html").write_text(desk_html)

    (data_out / "dates.json").write_text(
        json.dumps({"dates": summarise_cards(data_dir), "available": dates})
    )
    if (dest / "index.html").exists():
        shutil.copyfile(dest / "index.html", dest / "404.html")
    (dest / ".nojekyll").write_text("")
    return dest
