# CLAUDE.md — Harrogate Rentals Aggregator

A personal web app that aggregates rental listings from ~15 Harrogate letting agencies into a single filterable view.
Not public-facing — personal use only.

---

## Repo Structure

```
/
├── frontend/          # Vite + React + TypeScript (hosted on Netlify)
├── scraper/           # Python scraper (httpx + BeautifulSoup / Playwright)
├── netlify/
│   └── functions/     # Netlify Function for manual refresh trigger
└── .github/
    └── workflows/
        └── scrape.yml # Scheduled + manual GitHub Actions workflow
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

1. GitHub Actions triggers `scraper/main.py` on schedule or manual dispatch
2. Scraper upserts listings into Supabase using the service key
3. React frontend queries Supabase directly using the anon key (read-only)
4. Manual refresh button calls a Netlify Function, which triggers the workflow via GitHub API

---

## Database Schema

Table: `listings`

| Column       | Type        | Notes                                      |
|--------------|-------------|--------------------------------------------|
| id           | text        | Primary key — stable hash of agency + url  |
| agency       | text        |                                            |
| title        | text        |                                            |
| price        | integer     | Monthly rent in pence (avoid float)        |
| bedrooms     | integer     |                                            |
| url          | text        |                                            |
| image_url    | text        |                                            |
| scraped_at   | timestamptz | Set by scraper — use UTC                   |

- RLS is enabled.
- Anonymous reads are allowed (anon key is read-only).
- No auth layer on the frontend for now — not sharing the URL publicly.

---

## Scraper Conventions

- `id` should be a stable hash: `hashlib.md5(f"{agency}:{url}".encode()).hexdigest()`
- Use `httpx` by default; only reach for Playwright if the site requires JS rendering
- Upsert using Supabase's `upsert` with `on_conflict="id"`
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
- **Type for money** needs defining.
- **`datetime`** must be timezone-aware UTC.
- **Imports**: stdlib → third-party → local, separated by blank lines.

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

Detailed conventions for testing and docstrings live in `.claude/rules/` — load
the relevant file when working in that area.

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