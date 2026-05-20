'''
Whitaker Cadre — Harrogate residential lettings.

WordPress + PropertyHive, but unlike Verity Frearson the search results are fully
server-rendered. Page 1 is `/property-search/?{query}`; further pages are
`/property-search/page/N/?{query}`. We walk those page URLs directly until the
pagination's `.next` link is absent — no AJAX endpoint needed.

The site's search filters (`address_keyword`, `maximum_rent`, `availability`,
`department`) all apply server-side, so they're baked into `QUERY`. As a belt-and-braces
guard we also drop any card whose status isn't `availability-to-let` (excludes
`let-agreed` / `let`). All rents on the site are quoted PCM; a non-PCM card is dropped.
'''

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.whitakercadre.com'
QUERY = (
    'address_keyword=Harrogate'         # Harrogate listings only
    '&maximum_rent=1100'                # £1100 price cap
    '&availability=6'                   # available to let — excludes let-agreed
    '&department=residential-lettings'  # residential lettings, not sales/commercial
)
MAX_PAGES = 20

_BEDROOMS_RE = re.compile(r'(\d+)\s*Bedroom')
_PRICE_RE = re.compile(r'£\s*([\d,]+)')
_IMAGE_RE = re.compile(r'background-image:\s*url\(([^)]+)\)')


@dataclass
class WhitakerCadre:
    ''' Scraper for Whitaker Cadre lettings. '''

    agency: Agency = Agency.WHITAKER_CADRE

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Walk every page of the lettings search and return all listings. '''
        listings: list[RawListing] = []
        for page in range(1, MAX_PAGES + 1):
            if page == 1:
                url = f'{BASE_URL}/property-search/?{QUERY}'
            else:
                url = f'{BASE_URL}/property-search/page/{page}/?{QUERY}'
            response = client.get(url)
            response.raise_for_status()
            page_listings, has_next = _parse_page(response.text)
            listings.extend(page_listings)
            if not has_next:
                break
        return listings


def parse(html: str) -> list[RawListing]:
    ''' Parse one page of search results. Pure function — used by tests against fixtures. '''
    listings, _ = _parse_page(html)
    return listings


def _parse_page(html: str) -> tuple[list[RawListing], bool]:
    soup = BeautifulSoup(html, 'html.parser')
    cards = (_parse_card(card) for card in soup.select('li.type-property'))
    listings = [listing for listing in cards if listing is not None]
    has_next = soup.select_one('.propertyhive-pagination .next') is not None
    return listings, has_next


def _parse_card(card: Tag) -> RawListing | None:
    classes = card.get('class', [])
    if 'availability-to-let' not in classes:
        # Belt-and-braces: drop let-agreed / let cards the server filter should have excluded.
        return None

    price = _parse_price(card)
    if price is None:
        return None

    bedrooms = _parse_bedrooms(card)
    if bedrooms is None:
        return None

    return RawListing(
        agency=Agency.WHITAKER_CADRE,
        title=_parse_title(card),
        price=price,
        bedrooms=bedrooms,
        url=_parse_url(card),
        image_url=_parse_image_url(card),
    )


def _parse_title(card: Tag) -> str:
    link = card.select_one('h3 a')
    return ' '.join(link.get_text(' ', strip=True).split())


def _parse_url(card: Tag) -> str:
    return card.select_one('h3 a')['href']


def _parse_price(card: Tag) -> Pence | None:
    price_div = card.select_one('div.price')
    if price_div is None:
        return None
    text = price_div.get_text(' ', strip=True)
    # All site rents are PCM; skip anything quoted weekly so it can't slip past the cap.
    if 'pw' in text.lower():
        return None
    match = _PRICE_RE.search(text)
    if match is None:
        return None
    return Pence(int(match.group(1).replace(',', '')) * 100)


def _parse_bedrooms(card: Tag) -> int | None:
    # Several .icons spans per card (bed/bath); pick the one naming bedrooms.
    for span in card.select('span.icons'):
        match = _BEDROOMS_RE.search(span.get_text(' ', strip=True))
        if match is not None:
            return int(match.group(1))
    return None


def _parse_image_url(card: Tag) -> str | None:
    # image_url is genuinely optional in the model — a listing without an image is allowed.
    image_div = card.select_one('.wc-property-image')
    if image_div is None:
        return None
    match = _IMAGE_RE.search(image_div.get('style', ''))
    if match is None:
        return None
    return match.group(1).strip().strip('"\'')
