'''
Martin & Co — Harrogate residential lettings within a 5-mile radius.

Martin & Co runs on the same Belvoir Group / Property Jungle platform as `belvoir.py`, so
the same two quirks apply and force this scraper off the shared httpx client:

1. The site sits behind Cloudflare with TLS-fingerprint bot mitigation. Plain httpx is
   403'd (even on robots.txt). We use `curl_cffi` to impersonate Chrome's TLS stack.
2. We search by geographic `bounds` rather than the path slug — the `place=Harrogate`
   parameter is only a label. A browser `User-Agent` is sent alongside the Chrome TLS
   fingerprint to keep the query string intact.

The page is fully server-rendered; pagination uses a `/page-N/` path segment, walked until
a page renders zero cards. The `below-1100` path segment caps the price server-side.
Bedrooms aren't filterable in the search UI, so cards with fewer than one bedroom (garages,
single rooms) are dropped at parse time. Weekly (PW) rents would slip past the monthly cap,
so non-PCM cards are dropped too.

The honest-UA convention from `http.py` is intentionally broken here — the same trade-off
documented in `CLAUDE.md` and `belvoir.py`: volume is tiny, the data is publicly served and
robots.txt allows `/search-results/`.
'''

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag
from curl_cffi import requests as curl_requests

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.martinco.com'
SEARCH_PATH = '/search-results/for-letting/in-united-kingdom/below-1100'
MAX_PAGES = 20

# Chrome UA + Chrome TLS fingerprint (impersonate='chrome' below). See module docstring.
CHROME_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

# Bounding box for '5 miles around Harrogate' — copied verbatim from the live site's search
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
}

_BEDROOMS_RE = re.compile(r'(\d+)\s*bedroom', re.IGNORECASE)
_PRICE_RE = re.compile(r'£\s*([\d,]+)\s*(PCM|PW)', re.IGNORECASE)


@dataclass
class MartinAndCo:
    ''' Scraper for Martin & Co Harrogate lettings. '''

    agency: Agency = Agency.MARTIN_AND_CO

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        '''
        Walk every page of the lettings search and return all listings.

        The shared `httpx.Client` is ignored — Martin & Co needs a Chrome TLS fingerprint
        that plain httpx can't produce (see module docstring). We open a short-lived
        `curl_cffi` session instead.
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
    cards = soup.select('div.property--card__results')
    listings = [_parse_card(card) for card in cards]
    return [listing for listing in listings if listing is not None]


def _parse_card(card: Tag) -> RawListing | None:
    bedrooms = _parse_bedrooms(card)
    price = _parse_price(card)
    if bedrooms < 1 or price is None:
        return None
    return RawListing(
        agency=Agency.MARTIN_AND_CO,
        title=_parse_title(card),
        price=price,
        bedrooms=bedrooms,
        url=_parse_url(card),
        image_url=_parse_image_url(card),
    )


def _parse_bedrooms(card: Tag) -> int:
    type_div = card.select_one('div.property-type--search')
    match = _BEDROOMS_RE.search(type_div.get_text(' ', strip=True))
    return int(match.group(1)) if match else 0


def _parse_price(card: Tag) -> Pence | None:
    # Weekly rents would slip past the server-side £1100 cap — only accept PCM.
    text = card.select_one('div.property-price--search').get_text(' ', strip=True)
    match = _PRICE_RE.search(text)
    if match is None or match.group(2).upper() != 'PCM':
        return None
    return Pence(int(match.group(1).replace(',', '')) * 100)


def _parse_title(card: Tag) -> str:
    link = card.select_one('div.property-title--search a')
    # Source wraps the address mid-line, leaving a stray space before the comma.
    collapsed = ' '.join(link.get_text(' ', strip=True).split())
    return collapsed.replace(' ,', ',')


def _parse_url(card: Tag) -> str:
    return card.select_one('div.property-title--search a')['href']


def _parse_image_url(card: Tag) -> str | None:
    img = card.select_one('img.property--card__image')
    if img is None:
        return None
    return img.get('src')
