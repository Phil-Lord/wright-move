from pathlib import Path

import pytest

from scraper.agencies.fss import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'fss.html'


@pytest.fixture(scope='module')
def fss_html() -> str:
    return FIXTURE.read_text()


class TestParseFSS:
    def test_parse_returns_residential_listings_only(self, fss_html: str):
        listings = parse(fss_html)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_skips_garage_card(self, fss_html: str):
        # The page contains a £100/pcm garage card with no 'X Bed' heading; it must be filtered.
        listings = parse(fss_html)

        assert all('garage' not in listing.title.lower() for listing in listings)

    def test_parse_extracts_first_residential_listing(self, fss_html: str):
        # In this fixture the first non-garage card is a 1-bed flat at Bilton Park.
        listings = parse(fss_html)

        first = listings[0]

        assert first.agency is Agency.FSS
        assert first.title == 'Bilton Park, Bilton Lane, HG1 4DL'
        assert first.bedrooms == 1
        assert first.price == Pence(77500)
        assert first.url == (
            'https://www.fssproperty.co.uk/property-details/HAR190387/-/harrogate/bilton-lane'
        )
        assert first.image_url == 'https://www.fssproperty.co.uk/resize/HAR190387/0/0'

    def test_parse_prices_are_pence(self, fss_html: str):
        # All prices come back as pence — i.e. multiples of 100, never raw pound figures.
        listings = parse(fss_html)

        for listing in listings:
            assert listing.price >= 10000, f'{listing.title}: price {listing.price} too low for pence'
            assert listing.price % 100 == 0
