---
name: add-agency-scraper
description: >
  Add a new letting-agency scraper to the wright-move project. Use whenever the user asks to
  add a scraper for a specific agency, add a new agency, or wire up a new estate agency /
  letting agent — typically with a URL to that agency's search results page. Covers the full
  job end-to-end: investigating the site, picking a fetch strategy, writing the agency module
  + tests + fixture, registering the scraper, and updating the frontend so the new agency
  shows up in the UI.
---

# Adding a new agency scraper

Each agency lives in one module that returns `RawListing`s; id stamping, upsert and frontend
rendering are shared. This skill is the investigation methodology, the pattern decision tree
and the gotchas — everything else lives in `CLAUDE.md`, `.claude/rules/python-testing.md`
and the four existing scrapers (`fss`, `linley_and_simpson`, `verity_frearson`, `belvoir`),
which are the canonical templates to mirror.

---

## Phase 1 — Investigate

The shape of the scraper depends entirely on how the site serves listings. The implementation
is mechanical once you've worked out the pattern.

### 1.1 Check `robots.txt`

```bash
curl -s -A 'wright-move-scraper/0.1 (personal use)' 'https://www.example.co.uk/robots.txt'
```

If the search path is disallowed for `User-agent: *`, stop and tell the user — pick a
different entrypoint or skip the agency.

### 1.2 Fetch the user-provided URL and inspect

```bash
curl -s -A 'wright-move-scraper/0.1 (personal use)' 'URL' \
  -o /tmp/agency.html -w '%{http_code} %{size_download} %{url_effective}\n'
```

Look for:

- **Status**: 200 = good. 301 dropping query params from `Location` = the site strips params
  for non-browser UAs (see Pitfalls). 403 with "Just a moment…" body = Cloudflare
  bot-mitigation → Pattern D.
- **Property cards**: find the card container class
  (`grep -oE 'class="[^"]*(property|listing|card)[^"]*"' | sort -u`) and a per-card anchor.
- **Page title / canonical**: if the URL slug says Harrogate but the title says "United
  Kingdom", a filter parameter is being ignored.
- **JS-driven content**: empty body + lots of `<script>` tags = listings rendered
  client-side. Find the JSON endpoint in DevTools' network tab → Pattern C.

### 1.3 Find the site's filters

Push as much filtering to the server as possible. The wright-move defaults:

| Filter       | Default                                              |
|--------------|------------------------------------------------------|
| Price cap    | £1,100/month                                         |
| Min bedrooms | 1 (excludes garages, parking, rooms-in-shared-house) |
| Department   | Residential lettings (not commercial, not sales)     |
| Status       | Available (not "Let Agreed" / "Under Offer")         |

Try each filter in the agency's search UI and confirm it shows up in the URL. Then verify it
actually does something — some sites accept the parameter and ignore it (Verity Frearson's
`max-price` collapses results to zero). If a filter is broken, post-filter in Python and
comment why.

### 1.4 Find the pagination scheme

Common patterns: `?page=N`, `/page-N/`, `/N.html`, AJAX `current_page`, JSON `nbPages` /
`total`. Test page 2 by hand, then test a page that doesn't exist — if it 200s with zero
cards, your stop is "empty page"; if it 404s, "first error"; if it redirects to page 1,
track the active page explicitly. Always cap with `MAX_PAGES = 20`.

---

## Phase 2 — Pick the fetch pattern

If none of the four below fit because the site genuinely needs JS rendering, stop and ask
before adding Playwright — it's not yet a dependency, and most sites turn out to have a JSON
endpoint that avoids the need.

### Pattern A — Server-rendered HTML with simple pagination

**Example**: `agencies/fss.py`. Each page URL renders cards directly; walk `/N.html?{query}`
until the `next` link is absent. Push all filters into a `QUERY` constant.

### Pattern B — AJAX HTML fragments

**Example**: `agencies/verity_frearson.py`. WordPress + PropertyHive; the "Load More" button
POSTs to `wp-admin/admin-ajax.php` returning `{success, data: {html, max_pages}}`. Hit the
endpoint directly, parse the `html` fragment, stop at `max_pages`.

### Pattern C — JSON API endpoint

**Example**: `agencies/linley_and_simpson.py`. SPA frontend calls a JSON endpoint (find it
in DevTools) that returns structured hits — no HTML parsing. Push filters into the request:

```python
FILTERS = (
    '(search_type:lettings) AND (publish:true) AND (status:"To Let")'
    ' AND (search_areas:"harrogate") AND (price<=1100) AND (bedroom>=1)'
)
```

### Pattern D — Cloudflare-fronted (TLS-fingerprint blocking)

**Example**: `agencies/belvoir.py`. Plain `httpx` is 403'd with "Just a moment…" — Cloudflare
detects the TLS fingerprint as non-browser. Use `curl_cffi` to impersonate Chrome's TLS:

```python
from curl_cffi import requests as curl_requests

def scrape(self, client: httpx.Client) -> list[RawListing]:
    del client  # see module docstring — Belvoir needs its own session
    with curl_requests.Session(impersonate='chrome') as session:
        response = session.get(url, params=PARAMS, headers={'User-Agent': CHROME_UA})
```

The honest UA convention is intentionally broken here — document *why* in the module
docstring. `curl_cffi` ships its own bundled libcurl/BoringSSL, so CVE patches lag the OS;
pin a known-good version (`uv add` does this by default).

---

## Phase 3 — Implement

### 3.1 Add the enum member

Add a lowercase, underscore-separated value to `Agency` in `scraper/src/scraper/models.py`,
keeping the list alphabetical. The string is what gets written to the DB and shipped to the
frontend.

### 3.2 Create `agencies/<agency>.py`

Mirror whichever existing scraper matches your pattern. Required elements:

- Module docstring explaining the fetch strategy and any quirks (broken filters, redirects
  that strip params, weekly-vs-PCM handling).
- `@dataclass` class with `agency: Agency = Agency.X` and a `scrape(self, client: httpx.Client)
  -> list[RawListing]` method.
- A top-level `parse(html)` (or `parse(payload)` for JSON) — a **pure function** so unit tests
  can hit it without a network.
- Use the shared `httpx.Client` passed into `scrape` — except for Pattern D, where you open a
  `curl_cffi` session and `del client`.
- Prices as `Pence(pounds * 100)`. Never float.
- If the agency mixes PCM and PW, drop non-PCM rows in `_parse_card` by returning `None`,
  otherwise they slip past the price filter.
- No `id` or `last_seen` — those are stamped on later by `store.stamp()`.

Other code conventions (single quotes, British English, 100-char lines, type hints) are in
`CLAUDE.md`.

### 3.3 Register the scraper

Import the class and add an instance to `SCRAPERS` in `scraper/src/scraper/agencies/__init__.py`,
keeping the list alphabetical.

---

## Phase 4 — Test

### 4.1 Fixture

Hand-curate `scraper/tests/fixtures/<agency>.{html,json}` down to 2–3 stripped cards. See
`.claude/rules/python-testing.md` for size guidance; mirror `fss.html` or
`verity_frearson.html` for shape. Between the cards, cover:

- A simple straightforward listing
- A price with a thousands separator (£1,050) — most price regexes break on commas
- One edge case the scraper has to handle (PW rent, missing image, etc.)

### 4.2 Unit test

Mirror `tests/unit/agencies/test_verity_frearson.py`. Required test methods:

- `test_parse_returns_residential_listings`
- `test_parse_extracts_first_listing` (asserts on agency, title, price, bedrooms, url, image)
- `test_parse_handles_thousands_separator_in_price`
- `test_parse_prices_are_pence`
- `test_parse_returns_empty_for_empty_html`

Import from the direct module path, not the package re-export, so cmd-click resolves to the
definition.

### 4.3 Live sanity-check

Run the scraper end-to-end against the real site before committing. Don't trust unit tests
alone — fixtures can be stale. Then run the full suite (`pytest scraper/tests -q`).

---

## Phase 5 — Wire up the frontend

**Don't forget this step.** The DB write succeeds without it, but the new agency renders as
raw lowercase text (`belvoir` instead of `Belvoir`) in the UI.

Update both the `Agency` union AND the `AGENCY_NAMES` record in `frontend/src/types.ts`. The
record is `Record<Agency, string>` so a missing entry fails the TypeScript build — but the
union alone compiles fine and silently produces the lowercase render. Keep both alphabetical,
matching the Python `Agency` enum.

---

## Pitfalls (lessons from the existing scrapers)

- **Cloudflare TLS fingerprinting** — 403 + "Just a moment…" body. Detected by Client Hello
  fingerprint, not UA. Switch to `curl_cffi` with `impersonate='chrome'`. (Belvoir.)
- **Redirects strip query params for non-browser UAs** — same URL gives a small Harrogate
  result set in browser but a generic UK result from `curl`. Check the redirect chain with
  `curl -sI`; look for a 301 whose `Location` is missing the `?…`. Send a browser UA.
  (Belvoir.)
- **Filters accepted but ignored / collapsing to zero** — verify each filter actually returns
  the expected results. If broken, post-filter in Python and document the workaround. (Verity
  Frearson `max-price`.)
- **Weekly rents mixed with monthly** — `£300 PW` is roughly £1,300/month and slips past a
  `<= 1100` filter that compares against the indexed number. Filter at parse-time by checking
  `price_qualifier` / suffix text. (Linley & Simpson, Belvoir.)
- **Image lazyloading** — `src` is often a 1x1 placeholder or base64 GIF. The real URL lives
  in `data-src` (or `srcset`). Always prefer `data-src`. (Belvoir.)
- **Multiple elements matching the same selector inside one card** — e.g. Belvoir has two
  `.property-type` divs per card (Available-from + bedrooms). Iterate over all matches and
  pick the one your regex matches, rather than `select_one`.
- **Title text wrapping** — some sites wrap `<a>` content across lines so `text` ends up
  `"Mayfield Terrace, Harrogate\n,HG1"`. Collapse whitespace and clean stray ` ,` (see
  `fss._parse_title`).
- **Pagination loops** — out-of-range pages variously 200 with zero cards, redirect to page
  1, or 404. Always cap with `MAX_PAGES = 20` so a regression in stop-detection doesn't run
  forever.
