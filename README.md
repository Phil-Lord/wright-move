# Wright Move

A personal web app that aggregates rental listings from ~15 Harrogate letting agencies into a
single filterable view.

> Personal use only — the source is public, but the deployment isn't advertised, shared, or
> offered as a service for anyone else, so the live URL isn't published here.

---

## Stack

- **Frontend** — Vite + React + TypeScript, deployed on Netlify
- **Database** — Supabase (Postgres), a single `listings` table
- **Scraper** — Python (`httpx` + BeautifulSoup, Playwright where JS rendering is needed)
- **Scheduler** — GitHub Actions cron (every 30 mins, 8am–6pm UTC)
- **Manual refresh** — Netlify Function → GitHub API (`workflow_dispatch`)

---

## How it works

1. **Scrape** — GitHub Actions runs `python -m scraper` on a schedule (or on manual dispatch).
   One module per agency returns the listings it finds.
2. **Store** — the orchestrator stamps each listing with a stable `id` and `last_seen`, then
   upserts into Supabase using the service key.
3. **Read** — the React frontend queries Supabase directly with the read-only anon key and
   renders the listings as filterable cards linking back to each agency's site.
4. **Refresh** — the manual refresh button calls a Netlify Function, which triggers the scrape
   workflow via the GitHub API.

```
GitHub Actions ──> scraper ──> Supabase ──> React frontend (Netlify)
     ^                                              │
     └──────────── Netlify Function <── refresh ────┘
```

---

## Repo layout

```
frontend/   Vite + React + TypeScript app (Netlify)
scraper/    Python scrapers, one module per agency
netlify/    Netlify Functions (manual refresh trigger)
.github/    Scheduled + manual scrape workflow
supabase/   Database config
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture and conventions.

---

## Running locally

**Scraper:**

```bash
cd scraper
cp .env.example .env   # fill in SUPABASE_URL and SUPABASE_SERVICE_KEY
uv sync
uv run python -m scraper
```

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```
