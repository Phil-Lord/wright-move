from typing import Protocol

import httpx

from scraper.agencies.fss import FSS
from scraper.agencies.linley_and_simpson import LinleyAndSimpson
from scraper.agencies.verity_frearson import VerityFrearson
from scraper.models import Agency, RawListing


class Scraper(Protocol):
    agency: Agency

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Fetch and parse the agency's current listings. '''
        ...


SCRAPERS: list[Scraper] = [FSS(), LinleyAndSimpson(), VerityFrearson()]
