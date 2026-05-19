'''
Belvoir — Harrogate residential lettings within a 5-mile radius.

Belvoir is a national franchise; the local Harrogate office covers neighbouring villages too,
so we search by geographic bounds rather than by the path slug (`/in-harrogate/` only returns
the single office's stock and ignores the surrounding area). The page is fully server-rendered
into the same response — no AJAX, no JS — and pagination uses a `/page-N/` path segment.

Two quirks force this scraper off the shared httpx client:

1. Belvoir sits behind Cloudflare with TLS-fingerprint bot mitigation. Plain httpx hits the
   "Just a moment..." challenge and 403s. We use `curl_cffi` to impersonate Chrome's TLS
   stack — the request looks like Chrome at the wire layer.
2. The site's WordPress front controller issues a 301 that strips the query string unless the
   `User-Agent` looks like a browser. Without those query params (`bounds`, `place`, `radius`)
   the search collapses to a nationwide feed. So we send a Chrome UA too — consistent with the
   TLS fingerprint and the only way to keep the bounds filter active.

The honest-UA convention from `http.BUILD_CLIENT` is intentionally broken here. It's the same
trade-off documented in `CLAUDE.md`: switch to a browser UA only for sites that block
non-browser clients. Volume is tiny (one user, ~20 pages every 30 minutes); the data is
publicly served; robots.txt allows `/search-results/`.
'''

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag
from curl_cffi import requests as curl_requests

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.belvoir.co.uk'
SEARCH_PATH = '/search-results/for-letting/in-united-kingdom/below-1100'
MAX_PAGES = 20

# Chrome UA + Chrome TLS fingerprint (impersonate='chrome' below). See module docstring.
CHROME_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

# Bounding box for "5 miles around Harrogate" — copied verbatim from the live site's search
# UI so the result set matches what the browser would show for that preset.
BOUNDS = (
    r'{\"south\":53.96516165922786,\"west\":-1.581442903425881,'
    r'\"north\":54.02287134123327,\"east\":-1.4763865653142627}'
)
PARAMS = {
    'orderby': 'date_desc',
    'place': 'Harrogate, UK',
    'bounds': BOUNDS,
    'radius': '5',
    'department': 'residential',
}

_PRICE_RE = re.compile(r'£\s*([\d,]+)\s*(PCM|PW)', re.IGNORECASE)
_BEDROOMS_RE = re.compile(r'(\d+)\s*bedroom', re.IGNORECASE)


@dataclass
class Belvoir:
    ''' Scraper for Belvoir Harrogate lettings. '''

    agency: Agency = Agency.BELVOIR

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        '''
        Walk every page of the lettings search and return all listings.

        The shared `httpx.Client` is ignored — Belvoir needs a Chrome TLS fingerprint that
        plain httpx can't produce (see module docstring). We open a short-lived `curl_cffi`
        session instead.
        '''
        del client  # see docstring
        listings: list[RawListing] = []
        with curl_requests.Session(impersonate='chrome') as session:
            for page in range(1, MAX_PAGES + 1):
                response = session.get(
                    f'{BASE_URL}{SEARCH_PATH}/page-{page}/',
                    params=PARAMS,
                    headers={'User-Agent': CHROME_UA},
                    timeout=20,
                )
                response.raise_for_status()
                page_listings = parse(response.text)
                if not page_listings:
                    break
                listings.extend(page_listings)
        return listings


def parse(html: str) -> list[RawListing]:
    ''' Parse one page of search results. Pure function — used by tests against fixtures. '''
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    for card in soup.select('div.property--card__results'):
        listing = _parse_card(card)
        if listing is not None:
            listings.append(listing)
    return listings


def _parse_card(card: Tag) -> RawListing | None:
    # Weekly rents (PW) are in different units than our `<= £1100` cap implies — drop them
    # rather than risk mixing rent terms in the DB.
    price = _parse_price(card)
    if price is None:
        return None
    return RawListing(
        agency=Agency.BELVOIR,
        title=_parse_title(card),
        price=price,
        bedrooms=_parse_bedrooms(card),
        url=_parse_url(card),
        image_url=_parse_image_url(card),
    )


def _parse_title(card: Tag) -> str:
    return card.select_one('div.property-title a').get_text(' ', strip=True)


def _parse_url(card: Tag) -> str:
    return card.select_one('a.property--card__image-wrapper')['href']


def _parse_price(card: Tag) -> Pence | None:
    text = card.select_one('div.property-price').get_text(' ', strip=True)
    match = _PRICE_RE.search(text)
    if match is None or match.group(2).upper() != 'PCM':
        return None
    pounds = int(match.group(1).replace(',', ''))
    return Pence(pounds * 100)


def _parse_bedrooms(card: Tag) -> int:
    # Two `.property-type` divs per card: one nested in the price block (`Available from:
    # ...`) and one with the bedrooms (`N bedroom <type>`). Pick whichever matches.
    for type_div in card.select('div.property-type'):
        match = _BEDROOMS_RE.search(type_div.get_text(' ', strip=True))
        if match is not None:
            return int(match.group(1))
    return 0


def _parse_image_url(card: Tag) -> str | None:
    image = card.select_one('img.property--card__image')
    if image is None:
        return None
    return image.get('data-src') or None
