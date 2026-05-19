'''
William H Brown — Harrogate residential lettings.

The site runs on Homeflow's Ctesius platform: the search page ships as a raw Liquid
theme and renders property cards client-side. There's no separate JSON endpoint —
instead the server embeds the full result set in the page as a
`Ctesius.addConfig('properties', {...})` call. We fetch the search HTML and pull that
JSON blob out, so no browser is needed.

Filtering quirks:
- The price cap lives in the URL path. Homeflow's price dropdown jumps 1000 → 1110,
  so `up-to-1110` is the closest available rung to our £1,100 personal cap and is used
  as provided.
- Bedrooms and status aren't pushed to the URL, so 0-bed rows (rooms, parking) and
  `Let agreed` properties are dropped at parse time.
- Pagination is `?page=N`; the embedded `pagination.has_next_page` flag is the stop
  signal.
'''

import json
from dataclasses import dataclass
from typing import Any

import httpx

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.williamhbrown.co.uk'
SEARCH_URL = f'{BASE_URL}/north-yorkshire/harrogate/lettings/up-to-1110'
MAX_PAGES = 20

_PROPERTIES_MARKER = "Ctesius.addConfig('properties', "


@dataclass
class WilliamHBrown:
    ''' Scraper for William H Brown lettings. '''

    agency: Agency = Agency.WILLIAM_H_BROWN

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        '''Walk every page of the lettings search and return all listings.'''
        listings: list[RawListing] = []
        for page in range(1, MAX_PAGES + 1):
            response = client.get(SEARCH_URL, params={'page': page})
            response.raise_for_status()
            payload = _extract_payload(response.text)
            listings.extend(_parse_payload(payload))
            if not payload.get('pagination', {}).get('has_next_page'):
                break
        return listings


def parse(html: str) -> list[RawListing]:
    ''' Parse one page of search results. Pure function — used by tests against fixtures. '''
    return _parse_payload(_extract_payload(html))


def _extract_payload(html: str) -> dict[str, Any]:
    ''' Pull the embedded `Ctesius.addConfig('properties', {...})` JSON out of the page. '''
    marker = html.find(_PROPERTIES_MARKER)
    if marker == -1:
        return {}
    start = marker + len(_PROPERTIES_MARKER)
    # raw_decode stops at the end of the JSON object, ignoring the trailing `);` —
    # and handles braces inside strings, which a naive brace count would not.
    payload, _ = json.JSONDecoder().raw_decode(html, start)
    return payload


def _parse_payload(payload: dict[str, Any]) -> list[RawListing]:
    listings = []
    for prop in payload.get('properties', []):
        # Homeflow can list weekly (`pw`) rents; our price cap is monthly, so a weekly
        # rent would slip past it. Keep only monthly listings.
        if prop.get('price_qualifier') != 'pcm':
            continue
        # The URL price cap doesn't constrain bedrooms or status — drop 0-bed rows
        # (rooms, parking) and anything no longer available.
        if int(prop.get('bedrooms', 0)) < 1:
            continue
        if str(prop.get('status', '')).strip().lower() != 'to let':
            continue
        listings.append(_parse_property(prop))
    return listings


def _parse_property(prop: dict[str, Any]) -> RawListing:
    return RawListing(
        agency=Agency.WILLIAM_H_BROWN,
        title=prop['display_address'],
        price=Pence(int(prop['price_value']) * 100),
        bedrooms=int(prop['bedrooms']),
        url=f'{BASE_URL}{prop["property_url"]}',
        image_url=_parse_image_url(prop),
    )


def _parse_image_url(prop: dict[str, Any]) -> str | None:
    photo = prop.get('main_photo')
    if not photo:
        return None
    # Homeflow serves protocol-relative image URLs (`//mr0.homeflow-assets.co.uk/...`).
    return f'https:{photo}' if photo.startswith('//') else photo
