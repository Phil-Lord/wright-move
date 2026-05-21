from pathlib import Path

import pytest

from scraper.agencies.lentin_smith import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'lentin_smith.html'


@pytest.fixture(scope='module')
def lentin_smith_html() -> str:
    return FIXTURE.read_text()


class TestParseLentinSmith:
    def test_parse_returns_residential_listings(self, lentin_smith_html: str):
        listings = parse(lentin_smith_html)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_extracts_first_listing(self, lentin_smith_html: str):
        # In this fixture the first card is a 2-bed terraced on Chestnut Avenue.
        listings = parse(lentin_smith_html)

        first = listings[0]

        assert first.agency is Agency.LENTIN_SMITH
        assert first.title == 'Chestnut Avenue, Harrogate, North Yorkshire, HG1'
        assert first.bedrooms == 2
        assert first.price == Pence(105000)
        assert first.url == 'https://www.lentinsmith.co.uk/property-details.php?id=lentinsmith_10745519'
        assert first.image_url == (
            'https://www.lentinsmith.co.uk/property_images/lentinsmith_10745519_IMG_00.jpeg'
        )

    def test_parse_excludes_let_agreed_listings(self, lentin_smith_html: str):
        # The 'TOO LATE' card (St. Johns Grove) is let agreed and must be dropped.
        listings = parse(lentin_smith_html)

        assert all('St. Johns Grove' not in listing.title for listing in listings)
        assert len(listings) == 2

    def test_parse_handles_thousands_separator_in_price(self, lentin_smith_html: str):
        # Prices like £1,050 must be parsed without losing the thousands separator.
        listings = parse(lentin_smith_html)

        assert any(listing.price == Pence(105000) for listing in listings)

    def test_parse_prices_are_pence(self, lentin_smith_html: str):
        # All prices come back as pence — i.e. multiples of 100, never raw pound figures.
        listings = parse(lentin_smith_html)

        for listing in listings:
            assert listing.price >= 10000, (
                f'{listing.title}: price {listing.price} too low for pence'
            )
            assert listing.price % 100 == 0

    def test_parse_returns_empty_for_empty_html(self):
        assert parse('') == []
