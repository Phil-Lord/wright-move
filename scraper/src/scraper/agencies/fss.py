'''
Feather Smailes Scales (FSS) — Harrogate residential lettings.

The site uses Infinite Ajax Scroll to lazy-load further pages, but each page is also
fully server-rendered at `/search/N.html?...`. We walk those page URLs directly until
the pagination's `.next` link is absent — no browser needed.
'''

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.fssproperty.co.uk'
QUERY = (
    'instruction_type=Letting&department=Residential&bid=HAR'
    '&bedrooms=1'       # 1+ bedrooms — excludes garages/non-residential
    '&maxprice=1100'    # £1100 price cap
    '&orderby=price+asc'
)
MAX_PAGES = 20

_BEDROOMS_RE = re.compile(r'(\d+)\s*Bed')
_PRICE_RE = re.compile(r'£\s*([\d,]+)')
_IMAGE_RE = re.compile(r'background-image:\s*url\(([^)]+)\)')


@dataclass
class FSS:
    '''Scraper for Feather Smailes Scales lettings.'''

    agency: Agency = Agency.FSS

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        '''Walk every page of the lettings search and return all listings.'''
        listings: list[RawListing] = []
        for page in range(1, MAX_PAGES + 1):
            response = client.get(f'{BASE_URL}/search/{page}.html?{QUERY}')
            response.raise_for_status()
            page_listings, has_next = _parse_page(response.text)
            listings.extend(page_listings)
            if not has_next:
                break
        return listings


def parse(html: str) -> list[RawListing]:
    '''Parse one page of search results. Pure function — used by tests against fixtures.'''
    listings, _ = _parse_page(html)
    return listings


def _parse_page(html: str) -> tuple[list[RawListing], bool]:
    soup = BeautifulSoup(html, 'html.parser')
    listings = [_parse_card(card) for card in soup.select('div.property')]
    has_next = soup.select_one('.pagination .next') is not None
    return listings, has_next


def _parse_card(card: Tag) -> RawListing:
    return RawListing(
        agency=Agency.FSS,
        title=_parse_title(card),
        price=_parse_price(card),
        bedrooms=_parse_bedrooms(card),
        url=_parse_url(card),
        image_url=_parse_image_url(card),
    )


def _parse_bedrooms(card: Tag) -> int:
    heading = card.select_one('h4.thumbs-heading-four')
    return int(_BEDROOMS_RE.search(heading.get_text(' ', strip=True)).group(1))


def _parse_url(card: Tag) -> str:
    return f'{BASE_URL}{card["data-target"]}'


def _parse_title(card: Tag) -> str:
    link = card.select_one('div.thumbs-link h3 a')
    # Source HTML wraps lines mid-address, leaving stray space before commas after collapse.
    collapsed = ' '.join(link.get_text(' ', strip=True).split())
    return collapsed.replace(' ,', ',')


def _parse_price(card: Tag) -> Pence:
    # Two h3s per card: the title (wraps an <a>) and the price (no anchor).
    [heading] = [h for h in card.select('h3') if h.find('a') is None]
    pounds = int(_PRICE_RE.search(heading.get_text(' ', strip=True)).group(1).replace(',', ''))
    return Pence(pounds * 100)


def _parse_image_url(card: Tag) -> str | None:
    # image_url is genuinely optional in the model — a listing without an image is allowed.
    prop_img = card.select_one('div.prop-img')
    if prop_img is None:
        return None
    match = _IMAGE_RE.search(prop_img.get('style', ''))
    if match is None:
        return None
    path = match.group(1).strip().strip('"\'')
    return path if path.startswith('http') else f'{BASE_URL}{path}'
