import logging

from scraper.agencies import SCRAPERS
from scraper.http import build_client as build_http_client
from scraper.settings import load_settings
from scraper.store import build_client as build_db_client, now_utc, stamp, upsert

logger = logging.getLogger(__name__)


def run() -> None:
    ''' Run every registered scraper, isolating failures per agency. '''
    settings = load_settings()
    db_client = build_db_client(settings)
    scraped_at = now_utc()

    with build_http_client() as http_client:
        for scraper in SCRAPERS:
            agency = scraper.agency.value
            try:
                raw_listings = scraper.scrape(http_client)
            except Exception:
                logger.exception('scrape failed: %s', agency)
                continue

            listings = [stamp(raw, scraped_at) for raw in raw_listings]
            try:
                upsert(db_client, listings)
                logger.info('upserted %d listings: %s', len(listings), agency)
            except Exception:
                logger.exception('upsert failed: %s', agency)


def main() -> None:
    ''' CLI entrypoint — configure logging and run. '''
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    )
    run()


if __name__ == '__main__':
    main()
