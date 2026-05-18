# scraper

Python scraper that pulls rental listings from local letting agencies and upserts them into
the Supabase `listings` table. Runs on GitHub Actions (scheduled + manual).

## Run locally

```bash
cp .env.example .env   # fill in SUPABASE_URL and SUPABASE_SERVICE_KEY
uv sync
uv run python -m scraper
```

## Conventions

See `/CLAUDE.md` (root) for the full architecture and style rules, plus
`.claude/rules/python-testing.md` and `.claude/rules/python-docstrings.md`. Highlights:

- Python 3.12+ syntax (`str | None`, `list[T]`), single quotes, British English, 100-char lines.
- Two-stage models: agencies return `RawListing`; the orchestrator stamps `id` + `last_seen`
  to produce a `Listing` ready for upsert.
- Each agency is a module in `src/scraper/agencies/<agency>.py` exposing a `Scraper` (an
  `agency: Agency` attribute and `scrape(client) -> list[RawListing]`), registered in
  `agencies/__init__.SCRAPERS`.
- Split `fetch` from `parse(html: str) -> list[RawListing]` inside each agency module so
  parsing is pure and unit-testable against saved HTML fixtures in `tests/fixtures/`.
- Filter at the source (bake bedrooms/price into the search URL) rather than post-filtering.
- Check each site's `robots.txt` before adding a scraper.

## Layout

- `src/scraper/main.py` — orchestrator (runs each scraper, upserts, per-agency error isolation)
- `src/scraper/models.py` — `RawListing`, `Listing`, `Pence`, `Agency` enum
- `src/scraper/http.py` — shared `httpx.Client` factory with the project UA
- `src/scraper/store.py` — `stamp()` and Supabase upsert
- `src/scraper/settings.py` — env loading
- `src/scraper/agencies/` — one module per agency
- `tests/unit/`, `tests/integration/`, `tests/fixtures/`
