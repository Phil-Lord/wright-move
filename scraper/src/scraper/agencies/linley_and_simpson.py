'''
Linley & Simpson — Harrogate residential lettings.

The public search page is a Gatsby SPA whose property cards are populated client-side from
an Algolia-style search endpoint hosted at `linleyandsimpson-properties.q.starberry.com`.
We hit that JSON endpoint directly — no HTML parsing, no browser needed. Filters (status,
area, price, bedrooms) are pushed into the request so the response only contains rows we'd
keep anyway.
'''

from dataclasses import dataclass
from typing import Any

import httpx

from scraper.models import Agency, Pence, RawListing

SITE_URL = 'https://www.linleyandsimpson.co.uk'
SEARCH_URL = 'https://linleyandsimpson-properties.q.starberry.com/search'
HITS_PER_PAGE = 50
MAX_PAGES = 20

# Algolia-style filter string. Mirrors the filters the live site applies, plus our own
# personal thresholds. Note `price` and `bedroom` are numeric fields on the index.
FILTERS = (
    '(search_type:lettings) AND (publish:true) AND (status:"To Let")'
    ' AND (search_areas:"harrogate") AND (price<=1100) AND (bedroom>=1)'
)


@dataclass
class LinleyAndSimpson:
    '''Scraper for Linley & Simpson lettings.'''

    agency: Agency = Agency.LINLEY_AND_SIMPSON

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Walk every page of the search response and return all listings. '''
        listings: list[RawListing] = []
        for page in range(MAX_PAGES):
            params = {
                'query': '',
                'hitsPerPage': HITS_PER_PAGE,
                'page': page,
                'filters': FILTERS,
                'sort': 'sort_date_desc',
            }
            response = client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            listings.extend(_parse_hits(payload.get('hits', [])))
            if page + 1 >= payload.get('nbPages', 1):
                break
        return listings


def parse(payload: dict[str, Any]) -> list[RawListing]:
    '''Parse one page of search results. Pure function — used by tests against fixtures.'''
    return _parse_hits(payload.get('hits', []))


def _parse_hits(hits: list[dict[str, Any]]) -> list[RawListing]:
    parsed = []
    for hit in hits:
        # The site supports weekly (`pw`) rents too. Our price filter is in the same units
        # as the indexed `price` field, so a £1100/pw listing would slip through — skip
        # anything that isn't monthly to keep the comparison honest.
        if hit.get('price_qualifier') != 'pcm':
            continue
        parsed.append(_parse_hit(hit))
    return parsed


def _parse_hit(hit: dict[str, Any]) -> RawListing:
    return RawListing(
        agency=Agency.LINLEY_AND_SIMPSON,
        title=hit['display_address'],
        price=Pence(int(hit['price']) * 100),
        bedrooms=int(hit['bedroom']),
        url=f'{SITE_URL}/property-to-rent/{hit["slug"]}-{hit["objectID"]}/',
        image_url=_parse_image_url(hit),
    )


def _parse_image_url(hit: dict[str, Any]) -> str | None:
    images = hit.get('images') or []
    if not images:
        return None
    first = images[0]
    # Each image entry has size-keyed variants (`336x220`, `720x380`, ...) plus a `url`
    # original. Prefer the original; fall back to the largest preset we know about.
    for key in ('url', '720x380', '570x374', '336x220'):
        value = first.get(key)
        if value:
            return value
    return None
