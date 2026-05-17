# CLAUDE.md — Wright Move (Harrogate Rentals Aggregator)

A personal web app that aggregates rental listings from ~15 Harrogate letting agencies into a
single filterable view. Source is public, but the deployment is for personal use
only — not advertised, not shared, and not intended as a service for anyone else.

---

## Repo Structure

```
/
├── frontend/                       # Vite + React + TypeScript (hosted on Netlify)
├── scraper/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/scraper/
│   │   ├── main.py                 # orchestrator: run scrapers → upsert
│   │   ├── models.py               # RawListing, Listing, Pence, Agency
│   │   ├── http.py                 # shared httpx.Client factory
│   │   ├── store.py                # stamp() + Supabase upsert
│   │   ├── settings.py             # env loading
│   │   └── agencies/               # one module per agency, registered in __init__
│   └── tests/
├── netlify/
│   └── functions/                  # Netlify Function for manual refresh trigger
└── .github/
    └── workflows/
        └── scrape.yml              # Scheduled + manual GitHub Actions workflow
```

---

## Stack

- **Frontend**: Vite + React + TypeScript, deployed on Netlify
- **Database**: Supabase (Postgres) — listings table
- **Scraper**: Python with httpx + BeautifulSoup; Playwright where JS rendering is required
- **Scheduler**: GitHub Actions cron (every 30 mins, 8am–6pm UTC)
- **Manual refresh**: Netlify Function → GitHub API (`workflow_dispatch`)

---

## Data Flow

1. GitHub Actions runs `python -m scraper` on schedule or manual dispatch
2. Each agency scraper returns `RawListing`s; the orchestrator stamps `id` + `scraped_at`
   and upserts via Supabase using the service key
3. React frontend queries Supabase directly using the anon key (read-only)
4. Manual refresh button calls a Netlify Function, which triggers the workflow via GitHub API

---

## Database Schema

Table: `listings`

| Column       | Type        | Notes                                             |
|--------------|-------------|---------------------------------------------------|
| id           | text        | Primary key — stable hash of agency + url         |
| agency       | text        |                                                   |
| title        | text        |                                                   |
| price        | int4        | Monthly rent in pence (not numeric — avoid float) |
| bedrooms     | integer     |                                                   |
| url          | text        |                                                   |
| image_url    | text        |                                                   |
| scraped_at   | timestamptz | Set by scraper — use UTC                          |

- RLS is enabled.
- Anonymous reads are allowed (anon key is read-only).
- No auth layer on the frontend for now — not sharing the URL publicly.

---

## Scraper Conventions

### Architecture

- **Two-stage models**: scrapers return `RawListing` (what the site shows); the orchestrator
  in `main.py` calls `store.stamp()` to attach `id` + `scraped_at`, producing a `Listing`
  ready for upsert. Scrapers don't compute the id themselves.
- **`Agency` enum** (in `models.py`) — every agency gets a string-valued enum member, used
  as the `Scraper.agency` attribute and serialised straight to the DB column.
- **`Pence = NewType('Pence', int)`** in `models.py` is the money type. Avoid float.
- **Each agency module** lives in `src/scraper/agencies/<agency>.py` and exposes a class
  implementing the `Scraper` protocol (`agency: Agency`, `scrape(client) -> list[RawListing]`).
  Register the instance in `agencies/__init__.SCRAPERS`.
- **Split `fetch` from `parse`** inside each agency module so `parse(html: str) -> list[RawListing]`
  is a pure function, unit-testable against saved HTML fixtures.
- **Shared `httpx.Client`** from `http.build_client()` is passed into every scrape call — one
  pool, shared UA + timeouts.
- **Per-agency error isolation**: the orchestrator wraps each scraper + upsert in try/except so
  one broken site doesn't kill the run.
- Use `httpx` by default; only reach for Playwright if a site requires JS rendering.
- Upsert via Supabase's `upsert` with `on_conflict='id'`.
- **Filter at the source**: when an agency's search UI exposes filters (`bedrooms=`, `maxprice=`,
  property type, "available only" toggles, etc.), bake them into the agency's `QUERY` constant
  rather than scraping everything and post-filtering. Keeps the DB lean, cuts pages walked, and
  makes one source of truth for "what's eligible". Personal thresholds live as constants in the
  agency module (e.g. `bedrooms=1&maxprice=1100` in `fss.py`).
- **User-Agent policy**: send the honest `wright-move-scraper/<version> (personal use)` UA from
  `http.py`. Switch to a browser UA only for specific sites that block non-browser clients.
- **robots.txt**: check each agency's `robots.txt` before adding a scraper. If a path is
  disallowed for the catch-all (`User-agent: *`) crawler, don't scrape it — pick a different
  entrypoint or skip the agency. Re-check when adding new URL patterns to an existing agency.

### Style

- **Python 3.12+ syntax** — `str | None`, `list[Trade]`, `dict[str, Any]`. Never `Optional`,
  `Union`, `List`, `Dict` from `typing`.
- **Single quotes** for all strings, including docstrings.
- **100-character line limit**, PEP 8 otherwise.
- **British English** in code, comments, docs, and identifiers — `optimise`, `analyse`,
  `serialise`, `summarise`. Don't introduce `-ize` spellings.
- **Type hints required** on public function and method signatures. Use enums in type hints
  rather than `str` where a fixed value set exists.
- **Frozen dataclasses for domain models** — `@dataclass(frozen=True)`. Required fields first,
  defaulted last. `field(default_factory=...)` for mutable defaults.
- **String-compatible enums** for serialised values — `class Thing(str, Enum):`.
- **`datetime`** must be timezone-aware UTC.
- **Imports**: stdlib → third-party → local, separated by blank lines.

---

## Running the Scraper Locally

```bash
cd scraper
cp .env.example .env       # then fill in the values below
uv sync
uv run python -m scraper
```

Required environment variables (read by `settings.load_settings()`):

- `SUPABASE_URL` — Supabase project URL.
- `SUPABASE_SERVICE_KEY` — service-role key (write access — never commit, never expose to frontend).

In GitHub Actions these come from repo secrets; `.env` is for local dev only and is gitignored.

---

## Frontend Conventions

- TypeScript throughout — no `any` unless genuinely unavoidable
- Saved/hidden listings persisted (no user accounts)
- Web and mobile layout

---

## When to Ask vs Proceed

**Proceed without asking:**

- Adding/updating tests, fixing style, refactoring within a module
- Reading any file to gather context

**Ask first:**

- Changing public APIs (anything re-exported from a module's `__init__.py`)
- Adding new dependencies (`uv add <package>` — don't hand-edit `pyproject.toml`)
- Modifying `.env`, Dockerfile, or anything deployment-shaped

Detailed conventions for Python testing/docstrings and TypeScript live in
`.claude/rules/` — load the relevant file when working in that area.

---

## Current MVP Scope

- [ ] Listings as cards with direct link to agency site
- [ ] Basic filters: price range, bedrooms (could be done when scalping)
- [ ] Manual refresh button
- [ ] Mobile-friendly layout
- [ ] Saved/hidden listings

---

## Out of Scope

- User accounts / auth
- Saved searches or alerts
- Full listing detail pages
- Listing deduplication across agencies