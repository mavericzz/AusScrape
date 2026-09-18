from pathlib import Path

from src.dates import card_path, is_iso_date, list_card_dates, summarise_cards


def test_is_iso_date_accepts_day_pages_only():
    assert is_iso_date("2026-09-19")
    assert is_iso_date("2026-09-20")
    assert not is_iso_date("19-09-2026")
    assert not is_iso_date("2026-09-19/extra")


def test_list_card_dates_is_sorted_and_ignores_jev_dumps(tmp_path: Path):
    (tmp_path / "card_2026-09-20.json").write_text("{}")
    (tmp_path / "card_2026-09-19.json").write_text("{}")
    (tmp_path / "jev_2026-09-20.json").write_text("{}")
    assert list_card_dates(tmp_path) == ["2026-09-19", "2026-09-20"]
    assert card_path(tmp_path, "2026-09-19") == tmp_path / "card_2026-09-19.json"


def test_summarise_cards_exposes_best_bet_per_day(tmp_path: Path):
    (tmp_path / "card_2026-09-19.json").write_text(
        '{"date":"2026-09-19","meetings":[{},{}],"plays":[{}],'
        '"best_bet":{"name":"Portinari","venue":"Caulfield","race_number":4,"odds":4.2}}'
    )
    (tmp_path / "card_2026-09-20.json").write_text(
        '{"date":"2026-09-20","meetings":[{}],"plays":[],'
        '"best_bet":{"name":"Ginger Baker","venue":"Kalgoorlie","race_number":6,"odds":9.0}}'
    )
    rows = summarise_cards(tmp_path)
    assert [r["date"] for r in rows] == ["2026-09-19", "2026-09-20"]
    assert rows[0]["best_bet"]["name"] == "Portinari"
    assert rows[0]["meetings"] == 2
    assert rows[1]["href"] == "day/2026-09-20/"
