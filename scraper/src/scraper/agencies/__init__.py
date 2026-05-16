from typing import Protocol

import httpx

from scraper.models import Agency, RawListing


class Scraper(Protocol):
    agency: Agency

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Fetch and parse the agency's current listings. '''
        ...


SCRAPERS: list[Scraper] = []
