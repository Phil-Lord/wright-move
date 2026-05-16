from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType

Pence = NewType('Pence', int)


class Agency(str, Enum):
    ''' Letting agencies we scrape. String-valued for Supabase serialisation. '''

    FSS = 'fss'


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
        scraped_at (datetime): UTC timestamp of the scrape that produced this row.
        image_url (str | None): Primary listing image, if present.
    '''

    id: str
    agency: Agency
    title: str
    price: Pence
    bedrooms: int
    url: str
    scraped_at: datetime
    image_url: str | None = None
