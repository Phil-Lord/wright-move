from pathlib import Path

import pytest

from scraper.agencies.william_h_brown import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'william_h_brown.html'


@pytest.fixture(scope='module')
def william_h_brown_html() -> str:
    return FIXTURE.read_text()


class TestParseWilliamHBrown:
    def test_parse_returns_residential_listings(self, william_h_brown_html: str):
        listings = parse(william_h_brown_html)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_extracts_first_listing(self, william_h_brown_html: str):
        # In this fixture the first card is a 1-bed apartment on Back Dragon Parade.
        listings = parse(william_h_brown_html)

        first = listings[0]

        assert first.agency is Agency.WILLIAM_H_BROWN
        assert first.title == 'Back Dragon Parade, HARROGATE'
        assert first.bedrooms == 1
        assert first.price == Pence(85000)
        assert first.url == (
            'https://www.williamhbrown.co.uk/properties/21658399/lettings/P3033H5623-63624DDE'
        )
        assert first.image_url == (
            'https://mr0.homeflow-assets.co.uk/files/photo/image/47104/8203/500x375/Externall.jpg'
        )

    def test_parse_handles_thousands_separator_in_price(self, william_h_brown_html: str):
        # The £1,050 card must come back as 105000 pence, not lost to the comma.
        listings = parse(william_h_brown_html)

        assert any(listing.price == Pence(105000) for listing in listings)

    def test_parse_prices_are_pence(self, william_h_brown_html: str):
        listings = parse(william_h_brown_html)

        for listing in listings:
            assert listing.price >= 10000, (
                f'{listing.title}: price {listing.price} too low for pence'
            )
            assert listing.price % 100 == 0

    def test_parse_skips_weekly_rents(self, william_h_brown_html: str):
        # The Cold Bath Road card is priced per week — it must not slip past the monthly cap.
        listings = parse(william_h_brown_html)

        assert all('Cold Bath Road' not in listing.title for listing in listings)

    def test_parse_skips_let_agreed_listings(self, william_h_brown_html: str):
        # The Kings Road card is `Let agreed` — no longer available, so it's dropped.
        listings = parse(william_h_brown_html)

        assert all('Kings Road' not in listing.title for listing in listings)

    def test_parse_returns_empty_for_empty_html(self):
        assert parse('') == []
