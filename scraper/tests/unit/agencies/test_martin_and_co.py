from pathlib import Path

import pytest

from scraper.agencies.martin_and_co import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'martin_and_co.html'


@pytest.fixture(scope='module')
def martin_and_co_html() -> str:
    return FIXTURE.read_text()


class TestParseMartinAndCo:
    def test_parse_returns_residential_listings(self, martin_and_co_html: str):
        listings = parse(martin_and_co_html)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_extracts_first_listing(self, martin_and_co_html: str):
        # In this fixture the first card is a 2-bed flat on Willow Grove.
        listings = parse(martin_and_co_html)

        first = listings[0]

        assert first.agency is Agency.MARTIN_AND_CO
        assert first.title == 'Willow Grove, Harrogate'
        assert first.bedrooms == 2
        assert first.price == Pence(97500)
        assert first.url == (
            'https://www.martinco.com/properties-for-letting/'
            '2-bedrooms-flat-in-willow-grove-harrogate-hg1/100675000971/'
        )
        assert first.image_url and first.image_url.startswith('https://')

    def test_parse_handles_thousands_separator_in_price(self, martin_and_co_html: str):
        # Prices like £1,100 must be parsed without losing the thousands separator.
        listings = parse(martin_and_co_html)

        assert any(listing.price == Pence(110000) for listing in listings)

    def test_parse_skips_zero_bedroom_card(self, martin_and_co_html: str):
        # The fixture has a 0-bedroom HMO room; it must be filtered out.
        listings = parse(martin_and_co_html)

        assert all('hillside' not in listing.title.lower() for listing in listings)

    def test_parse_skips_weekly_rent_card(self, martin_and_co_html: str):
        # A £250 PW card would slip past the £1100 monthly cap; non-PCM cards are dropped.
        listings = parse(martin_and_co_html)

        assert all('station parade' not in listing.title.lower() for listing in listings)

    def test_parse_prices_are_pence(self, martin_and_co_html: str):
        # All prices come back as pence — i.e. multiples of 100, never raw pound figures.
        listings = parse(martin_and_co_html)

        for listing in listings:
            assert listing.price >= 10000, (
                f'{listing.title}: price {listing.price} too low for pence'
            )
            assert listing.price % 100 == 0

    def test_parse_returns_empty_for_empty_html(self):
        assert parse('') == []
