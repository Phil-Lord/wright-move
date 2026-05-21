'''
Lentin Smith — Harrogate residential lettings.

The site serves a single server-rendered 'search-gallery' page that lists every
matching property at once — there's no pagination to walk. Price filtering works
at the source (`pricemin` / `pricemax` in the query), so we bake the £1100 cap in.

The search UI has no 'available only' toggle: let-agreed properties stay in the
results with a 'TOO LATE' overlay and an `Available: TOO LATE` line in the card.
We drop those at parse-time, along with any non-PCM (weekly) rents, by returning
`None` from `_parse_card`. Minimum bedrooms is post-filtered in Python since the
gallery URL exposes no bedroom parameter.
'''

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.lentinsmith.co.uk'
QUERY = (
    'locations[]=Harrogate'
    '&pricemin=0'
    '&pricemax=1100'    # £1100 price cap — enforced server-side
    '&ddm_order=2'      # sort by price ascending
)
MIN_BEDROOMS = 1

_PRICE_RE = re.compile(r'£\s*([\d,]+)')
_BEDROOMS_RE = re.compile(r'(\d+)\s*Bedroom')


@dataclass
class LentinSmith:
    ''' Scraper for Lentin Smith lettings. '''

    agency: Agency = Agency.LENTIN_SMITH

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Fetch the single search-gallery page and return all available listings. '''
        response = client.get(f'{BASE_URL}/search-gallery.php?{QUERY}')
        response.raise_for_status()
        return parse(response.text)


def parse(html: str) -> list[RawListing]:
    ''' Parse the search-gallery page. Pure function — used by tests against fixtures. '''
    soup = BeautifulSoup(html, 'html.parser')
    listings = [_parse_card(card) for card in soup.select('div.property')]
    return [
        listing for listing in listings
        if listing is not None and listing.bedrooms >= MIN_BEDROOMS
    ]


def _parse_card(card: Tag) -> RawListing | None:
    # Let-agreed properties keep an 'Available: TOO LATE' line — drop them.
    if 'TOO LATE' in card.get_text():
        return None
    price = _parse_price(card)
    if price is None:
        return None
    return RawListing(
        agency=Agency.LENTIN_SMITH,
        title=_parse_title(card),
        price=price,
        bedrooms=_parse_bedrooms(card),
        url=_parse_url(card),
        image_url=_parse_image_url(card),
    )


def _parse_title(card: Tag) -> str:
    return card.select_one('div.propertyDetails h2').get_text(strip=True)


def _parse_price(card: Tag) -> Pence | None:
    text = card.select_one('p.price').get_text(' ', strip=True)
    # Skip weekly rents — '£300 pw' is ~£1300/month and would slip past the cap.
    if 'pw' in text.lower():
        return None
    pounds = int(_PRICE_RE.search(text).group(1).replace(',', ''))
    return Pence(pounds * 100)


def _parse_bedrooms(card: Tag) -> int:
    text = card.select_one('div.description h3').get_text(' ', strip=True)
    match = _BEDROOMS_RE.search(text)
    return int(match.group(1)) if match else 0


def _parse_url(card: Tag) -> str:
    # The card link carries the active search params; rebuild a clean, stable
    # detail URL from the `id` param so the stamped listing id doesn't churn
    # when the search query changes.
    href = card.select_one('div.thumbnail a')['href']
    ids = parse_qs(urlparse(href).query).get('id')
    if ids:
        return f'{BASE_URL}/property-details.php?id={ids[0]}'
    return href if href.startswith('http') else f'{BASE_URL}/{href.lstrip("/")}'


def _parse_image_url(card: Tag) -> str | None:
    image = card.select_one('div.thumbnail a img')
    if image is None or not image.get('src'):
        return None
    src = image['src']
    return src if src.startswith('http') else f'{BASE_URL}/{src.lstrip("/")}'
