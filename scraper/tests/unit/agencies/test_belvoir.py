from pathlib import Path

import pytest

from scraper.agencies.belvoir import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'belvoir.html'


@pytest.fixture(scope='module')
def belvoir_html() -> str:
    return FIXTURE.read_text()


class TestParseBelvoir:
    def test_parse_returns_pcm_listings_and_skips_weekly(self, belvoir_html: str):
        # Fixture has 3 cards: 2 PCM, 1 PW. Weekly rents are dropped to avoid mixing units.
        listings = parse(belvoir_html)

        assert len(listings) == 2
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_extracts_first_listing(self, belvoir_html: str):
        # First card in the fixture is a 1-bed flat on Victoria Road at £825 PCM.
        listings = parse(belvoir_html)

        first = listings[0]

        assert first.agency is Agency.BELVOIR
        assert first.title == 'Victoria Road, Harrogate, HG2'
        assert first.bedrooms == 1
        assert first.price == Pence(82500)
        assert first.url == (
            'https://www.belvoir.co.uk/properties-for-letting/'
            '1-bedroom-flat-in-victoria-road-harrogate-hg2/66866371-2309/'
        )
        assert first.image_url and first.image_url.startswith('https://')

    def test_parse_handles_thousands_separator_in_price(self, belvoir_html: str):
        # Second card is £1,050 PCM — the comma must not split the price parse.
        listings = parse(belvoir_html)

        assert listings[1].price == Pence(105000)

    def test_parse_prices_are_pence(self, belvoir_html: str):
        # All prices come back as pence — multiples of 100, never raw pound figures.
        listings = parse(belvoir_html)

        for listing in listings:
            assert listing.price >= 10000, (
                f'{listing.title}: price {listing.price} too low for pence'
            )
            assert listing.price % 100 == 0

    def test_parse_returns_empty_for_empty_html(self):
        assert parse('') == []
