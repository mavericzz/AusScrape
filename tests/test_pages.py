from pathlib import Path

from src.pages import build_static_site


def test_build_static_site_writes_date_pages_and_money(tmp_path: Path):
    root = tmp_path / "repo"
    frontend = root / "frontend"
    data = root / "data"
    frontend.mkdir(parents=True)
    data.mkdir()
    frontend.joinpath("index.html").write_text(
        '<html><head>\n  <base href="/" />\n  <link rel="stylesheet" href="styles.css" />\n</head><body>index</body></html>\n'
    )
    frontend.joinpath("desk.html").write_text(
        '<html><head>\n  <base href="/" />\n  <script src="app.js"></script>\n</head><body>desk</body></html>\n'
    )
    frontend.joinpath("styles.css").write_text("body{color:black}")
    frontend.joinpath("app.js").write_text("console.log(1)")
    frontend.joinpath("index.js").write_text("console.log(2)")
    frontend.joinpath("site.js").write_text("console.log(3)")
    data.joinpath("card_2026-09-19.json").write_text(
        '{"date":"2026-09-19","meetings":[{"venue":"Caulfield","races":[{"race_number":1,'
        '"runners":[{"name":"Fav","odds":2.0},{"name":"Second","odds":4.0}]}]}],'
        '"plays":[{"name":"Fav","venue":"Caulfield","race_number":1}],'
        '"best_bet":{"name":"Fav","venue":"Caulfield","race_number":1}}'
    )
    dest = tmp_path / "dist"
    out = build_static_site(root, dest, base_href="/AusScrape/")
    assert out == dest
    index = (dest / "index.html").read_text()
    assert 'href="/AusScrape/"' in index
    day = dest / "day" / "2026-09-19" / "index.html"
    assert day.exists()
    assert 'href="/AusScrape/"' in day.read_text()
    payload = (dest / "data" / "dates.json").read_text()
    assert "2026-09-19" in payload
    assert "day/2026-09-19/" in payload
    card = (dest / "data" / "card_2026-09-19.json").read_text()
    assert '"money_bet"' in card
    assert (dest / ".nojekyll").exists()
