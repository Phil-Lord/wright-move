'''
Verity Frearson — Harrogate residential lettings.

The public search page is a WordPress (PropertyHive) site with a JS-driven "Load More"
button. Property cards are rendered server-side and progressively fetched via a single
`admin-ajax.php` endpoint with `action=load_properties`. We hit that endpoint directly
and parse the returned HTML fragment — no browser needed.

Price filtering at the source is broken on this site: any `min-price` / `max-price`
value (sent via the search UI, the page URL, or the AJAX endpoint) collapses the result
set to zero. We work around it by sourcing the unfiltered Harrogate Lettings feed and
post-filtering by price in Python. The filters that *do* work (`buy-let`, `keyword-search`,
`sold-included`, `min-bedrooms`) are baked into the request so we don't pull let-agreed
rows or non-residential listings.
'''

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

from scraper.models import Agency, Pence, RawListing

BASE_URL = 'https://www.verityfrearson.co.uk'
AJAX_URL = f'{BASE_URL}/wp-admin/admin-ajax.php'
MAX_PAGES = 20

# £1100 cap, enforced in Python because the site's price filter returns zero hits
# for any value (see module docstring).
MAX_PRICE = Pence(110000)

# Filters that actually work on the AJAX endpoint. `sold-included=false` strips
# "Let Agreed" rows; `min-bedrooms=1` excludes parking/garage-only listings.
BASE_PARAMS = {
    'action': 'load_properties',
    'buy-let': 'Lettings',
    'keyword-search': 'Harrogate',
    'sold-included': 'false',
    'min-bedrooms': '1',
    'max-bedrooms': '',
    'property-type': '',
    'min-price': '',
    'max-price': '',
    'filter-properties': 'DESC',
}

_PRICE_RE = re.compile(r'£\s*([\d,]+)')
_BEDROOMS_RE = re.compile(r'(\d+)\s*Bedroom')
_IMAGE_RE = re.compile(r"background-image:\s*url\(['\"]?([^'\")]+)['\"]?\)")


@dataclass
class VerityFrearson:
    '''Scraper for Verity Frearson lettings.'''

    agency: Agency = Agency.VERITY_FREARSON

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Walk every page of the load-more AJAX feed and return all listings. '''
        listings: list[RawListing] = []
        # `current_page` is "the page already on screen"; the response
        # returns the next one. Start at 0 to request page 1.
        for page in range(MAX_PAGES):
            data = {**BASE_PARAMS, 'current_page': str(page)}
            response = client.post(AJAX_URL, data=data)
            response.raise_for_status()
            payload = response.json()
            if not payload.get('success'):
                break
            body = payload.get('data') or {}
            listings.extend(parse(body.get('html', '')))
            max_pages = int(body.get('max_pages') or 0)
            if page + 1 >= max_pages:
                break
        return [listing for listing in listings if listing.price <= MAX_PRICE]


def parse(html: str) -> list[RawListing]:
    ''' Parse a page of property-card HTML. Pure function — used by tests against fixtures. '''
    soup = BeautifulSoup(html, 'html.parser')
    return [_parse_card(card) for card in soup.select('div.b-property')]


def _parse_card(card: Tag) -> RawListing:
    return RawListing(
        agency=Agency.VERITY_FREARSON,
        title=_parse_title(card),
        price=_parse_price(card),
        bedrooms=_parse_bedrooms(card),
        url=_parse_url(card),
        image_url=_parse_image_url(card),
    )


def _parse_title(card: Tag) -> str:
    return card.select_one('h3.b-property__title').get_text(strip=True)


def _parse_price(card: Tag) -> Pence:
    text = card.select_one('div.b-property__content__price').get_text(' ', strip=True)
    pounds = int(_PRICE_RE.search(text).group(1).replace(',', ''))
    return Pence(pounds * 100)


def _parse_bedrooms(card: Tag) -> int:
    text = card.select_one('div.b-property__content__bedrooms').get_text(' ', strip=True)
    return int(_BEDROOMS_RE.search(text).group(1))


def _parse_url(card: Tag) -> str:
    return card.select_one('a.b-property__property-link')['href']


def _parse_image_url(card: Tag) -> str | None:
    image = card.select_one('div.b-property__image-container__image')
    if image is None:
        return None
    match = _IMAGE_RE.search(image.get('style', ''))
    return match.group(1).strip() if match else None
