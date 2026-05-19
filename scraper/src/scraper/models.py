from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType

Pence = NewType('Pence', int)


class Agency(str, Enum):
    ''' Letting agencies we scrape. String-valued for Supabase serialisation. '''

    BELVOIR = 'belvoir'
    FSS = 'fss'
    LINLEY_AND_SIMPSON = 'linley_and_simpson'
    VERITY_FREARSON = 'verity_frearson'


@dataclass(frozen=True)
class RawListing:
    '''
    A listing as parsed from an agency's site, before storage stamping.

    Attributes:
        agency (Agency): Source agency.
        title (str): Listing title.
        price (Pence): Monthly rent in pence.
        bedrooms (int): Number of bedrooms.
        url (str): Direct link to the agency's listing page.
        image_url (str | None): Primary listing image, if present.
    '''

    agency: Agency
    title: str
    price: Pence
    bedrooms: int
    url: str
    image_url: str | None = None


@dataclass(frozen=True)
class Listing:
    '''
    A storage-ready listing with id and scrape timestamp stamped on.

    Attributes:
        id (str): md5 of '{agency}:{url}' — stable across runs.
        agency (Agency): Source agency.
        title (str): Listing title.
        price (Pence): Monthly rent in pence.
        bedrooms (int): Number of bedrooms.
        url (str): Direct link to the agency's listing page.
        last_seen (datetime): UTC timestamp of the most recent scrape that saw this row.
        image_url (str | None): Primary listing image, if present.

    Note:
        `first_seen` is DB-managed (default now() on insert, preserved on conflict)
        and is intentionally excluded — the scraper neither sets nor reads it.
    '''

    id: str
    agency: Agency
    title: str
    price: Pence
    bedrooms: int
    url: str
    last_seen: datetime
    image_url: str | None = None
