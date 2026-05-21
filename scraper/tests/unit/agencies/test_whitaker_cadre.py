from pathlib import Path

import pytest

from scraper.agencies.whitaker_cadre import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'whitaker_cadre.html'


@pytest.fixture(scope='module')
def whitaker_cadre_html() -> str:
    return FIXTURE.read_text()


class TestParseWhitakerCadre:
    def test_parse_returns_residential_listings(self, whitaker_cadre_html: str):
        listings = parse(whitaker_cadre_html)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_skips_let_agreed_card(self, whitaker_cadre_html: str):
        # The fixture's third card is `availability-let-agreed` and must be excluded.
        listings = parse(whitaker_cadre_html)

        assert all('cold-bath-road' not in listing.url for listing in listings)

    def test_parse_extracts_first_listing(self, whitaker_cadre_html: str):
        listings = parse(whitaker_cadre_html)

        first = listings[0]

        assert first.agency is Agency.WHITAKER_CADRE
        assert first.title == 'Spring Grove, Harrogate'
        assert first.price == Pence(63500)
        assert first.bedrooms == 1
        assert first.url == 'https://www.whitakercadre.com/property/spring-grove-harrogate/'
        assert first.image_url == (
            'https://www.whitakercadre.com/wp-content/uploads/2026/05/spring-grove.jpg'
        )

    def test_parse_handles_thousands_separator_in_price(self, whitaker_cadre_html: str):
        # The second card is quoted at £1,050 pcm — the comma must not break the price regex.
        listings = parse(whitaker_cadre_html)

        kings_road = next(listing for listing in listings if 'kings-road' in listing.url)

        assert kings_road.price == Pence(105000)

    def test_parse_prices_are_pence(self, whitaker_cadre_html: str):
        listings = parse(whitaker_cadre_html)

        for listing in listings:
            assert listing.price >= 10000, f'{listing.title}: {listing.price} too low for pence'
            assert listing.price % 100 == 0

    def test_parse_returns_empty_for_empty_html(self):
        assert parse('<html><body></body></html>') == []
