from pathlib import Path

import pytest

from scraper.agencies.verity_frearson import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'verity_frearson.html'


@pytest.fixture(scope='module')
def verity_frearson_html() -> str:
    return FIXTURE.read_text()


class TestParseVerityFrearson:
    def test_parse_returns_residential_listings(self, verity_frearson_html: str):
        listings = parse(verity_frearson_html)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_extracts_first_listing(self, verity_frearson_html: str):
        # In this fixture the first card is a 2-bed terraced house on Mayfield Terrace.
        listings = parse(verity_frearson_html)

        first = listings[0]

        assert first.agency is Agency.VERITY_FREARSON
        assert first.title == 'Mayfield Terrace, Harrogate, HG1'
        assert first.bedrooms == 2
        assert first.price == Pence(95000)
        assert first.url == 'https://www.verityfrearson.co.uk/properties/mayfield-terrace-harrogate-hg1/'
        assert first.image_url and first.image_url.startswith('https://')

    def test_parse_handles_thousands_separator_in_price(self, verity_frearson_html: str):
        # Prices like £1,250 must be parsed without losing the thousands separator.
        listings = parse(verity_frearson_html)

        assert any(listing.price >= Pence(100000) for listing in listings)

    def test_parse_prices_are_pence(self, verity_frearson_html: str):
        # All prices come back as pence — i.e. multiples of 100, never raw pound figures.
        listings = parse(verity_frearson_html)

        for listing in listings:
            assert listing.price >= 10000, (
                f'{listing.title}: price {listing.price} too low for pence'
            )
            assert listing.price % 100 == 0

    def test_parse_returns_empty_for_empty_html(self):
        assert parse('') == []
