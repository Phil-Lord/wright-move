import httpx

# Honest UA so site admins can identify our traffic in their logs:
# - name + version lets them correlate behaviour with a release
# - '(personal use)' signals we're not a commercial scraper
# Swap to a browser UA only for sites that block non-browser clients.
USER_AGENT = 'wright-move-scraper/0.1 (personal use)'


def build_client() -> httpx.Client:
    ''' Return an httpx client with shared defaults: UA, timeouts, redirects. '''
    return httpx.Client(
        headers={'User-Agent': USER_AGENT},
        timeout=httpx.Timeout(15.0),
        follow_redirects=True,
    )
