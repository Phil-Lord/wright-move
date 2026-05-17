# frontend

Vite + React + TypeScript app that reads from the Supabase `listings` table and renders a
filterable grid of rental cards. Deployed on Netlify.

## Run locally

```bash
pnpm install
cp .env.example .env   # fill in VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
pnpm dev
```

## Conventions

See `/CLAUDE.md` (root) for project-wide rules and `.claude/rules/typescript.md` for TS style.
Key points: single quotes, no semicolons, snake_case DB column names preserved on the wire,
`null` (not `undefined`) for nullable columns, prices as pence (`number`).

## Layout

- `src/supabase.ts` — client, reads `VITE_SUPABASE_*` env vars
- `src/useListings.ts` — query hook
- `src/types.ts` — hand-mirrored from `scraper/src/scraper/models.py`
- `src/format.ts` — money/date formatters (`formatPrice` owns pence → £X pcm)
- `src/ListingCard.tsx`, `src/App.tsx` — UI
