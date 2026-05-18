import hashlib
from datetime import UTC, datetime

from supabase import Client, create_client

from scraper.models import Listing, RawListing
from scraper.settings import Settings


def build_client(settings: Settings) -> Client:
    ''' Construct a Supabase client using the service-role key. '''
    return create_client(settings.supabase_url, settings.supabase_service_key)


def now_utc() -> datetime:
    ''' UTC timestamp for the current scrape run. '''
    return datetime.now(UTC)


def stamp(raw: RawListing, last_seen: datetime) -> Listing:
    ''' Attach the storage fields (id, last_seen) to a RawListing. '''
    listing_id = hashlib.md5(f'{raw.agency.value}:{raw.url}'.encode()).hexdigest()
    return Listing(
        id=listing_id,
        agency=raw.agency,
        title=raw.title,
        price=raw.price,
        bedrooms=raw.bedrooms,
        url=raw.url,
        last_seen=last_seen,
        image_url=raw.image_url,
    )


def upsert(client: Client, listings: list[Listing]) -> None:
    '''
    Upsert listings into the `listings` table, keyed by id.

    `first_seen` is deliberately omitted from the payload as the DB column has a
    `default now()` for inserts, and PostgREST's upsert leaves columns absent
    from the body untouched on conflict — so the original value is preserved
    across subsequent scrapes.
    '''
    if not listings:
        return
    rows = [
        {
            'id': listing.id,
            'agency': listing.agency.value,
            'title': listing.title,
            'price': int(listing.price),
            'bedrooms': listing.bedrooms,
            'url': listing.url,
            'image_url': listing.image_url,
            'last_seen': listing.last_seen.isoformat(),
        }
        for listing in listings
    ]
    client.table('listings').upsert(rows, on_conflict='id').execute()
