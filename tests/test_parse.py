from src.parse import horse_key, parse_margin, parse_sp, parse_weight, venue_key


def test_horse_key_strips_country_suffix_and_punctuation():
    assert horse_key("Cradle Of Jazz (NZ)") == "cradleofjazz"
    assert horse_key("Headwall") == horse_key(" head-wall ")


def test_venue_key_normalises_racing_com_slugs():
    assert venue_key("bet365-bairnsdale") == "bairnsdale"
    assert venue_key("Royal Randwick") == "royalrandwick"
    assert venue_key("ladbrokes-pioneer-park") == "pioneerpark"


def test_parse_helpers_read_racing_com_units():
    assert parse_weight("56kg") == 56.0
    assert parse_margin("2.15L") == 2.15
    assert parse_sp("$$8.50") == 8.5
