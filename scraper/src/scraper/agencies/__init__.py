from typing import Protocol

import httpx

from scraper.agencies.belvoir import Belvoir
from scraper.agencies.fss import FSS
from scraper.agencies.lentin_smith import LentinSmith
from scraper.agencies.linley_and_simpson import LinleyAndSimpson
from scraper.agencies.martin_and_co import MartinAndCo
from scraper.agencies.verity_frearson import VerityFrearson
from scraper.agencies.whitaker_cadre import WhitakerCadre
from scraper.agencies.william_h_brown import WilliamHBrown
from scraper.models import Agency, RawListing


class Scraper(Protocol):
    agency: Agency

    def scrape(self, client: httpx.Client) -> list[RawListing]:
        ''' Fetch and parse the agency's current listings. '''
        ...


SCRAPERS: list[Scraper] = [
    Belvoir(),
    FSS(),
    LentinSmith(),
    LinleyAndSimpson(),
    MartinAndCo(),
    VerityFrearson(),
    WhitakerCadre(),
    WilliamHBrown(),
]
