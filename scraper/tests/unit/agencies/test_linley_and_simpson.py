import json
from pathlib import Path

import pytest

from scraper.agencies.linley_and_simpson import parse
from scraper.models import Agency, Pence


FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'linley_and_simpson.json'


@pytest.fixture(scope='module')
def search_payload() -> dict:
    return json.loads(FIXTURE.read_text())


class TestParseLinleyAndSimpson:
    def test_parse_returns_residential_listings_only(self, search_payload: dict):
        listings = parse(search_payload)

        assert listings, 'expected at least one listing'
        assert all(listing.bedrooms >= 1 for listing in listings)

    def test_parse_skips_non_monthly_prices(self, search_payload: dict):
        # Given a payload where one hit is a per-week rent
        payload = {'hits': [
            {**search_payload['hits'][0], 'price_qualifier': 'pw'},
            search_payload['hits'][1],
        ]}

        listings = parse(payload)

        # Then only the pcm hit is returned
        assert len(listings) == 1
        assert listings[0].title == search_payload['hits'][1]['display_address']

    def test_parse_extracts_first_listing(self, search_payload: dict):
        # In this fixture the first hit is a 2-bed apartment on Station Parade.
        listings = parse(search_payload)

        first = listings[0]

        assert first.agency is Agency.LINLEY_AND_SIMPSON
        assert first.title == 'Station Parade, Harrogate, North Yorkshire, HG1'
        assert first.bedrooms == 2
        assert first.price == Pence(110000)
        assert first.url == (
            'https://www.linleyandsimpson.co.uk/property-to-rent/'
            '2-bedroom-apartment-to-rent-in-station-parade-harrogate-north-yorkshire-hg1'
            '-69fb05989c4d13cbd580c110/'
        )
        assert first.image_url and first.image_url.startswith('https://')

    def test_parse_prices_are_pence(self, search_payload: dict):
        # All prices come back as pence — i.e. multiples of 100, never raw pound figures.
        listings = parse(search_payload)

        for listing in listings:
            assert listing.price >= 10000, (
                f'{listing.title}: price {listing.price} too low for pence'
            )
            assert listing.price % 100 == 0
