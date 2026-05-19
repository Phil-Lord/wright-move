# TypeScript Conventions

Reference for TypeScript code in this project (currently `frontend/` only).

---

## Style

- **Single quotes** for all strings.
- **No semicolons** — relies on ASI; matches the existing Vite scaffold.
- **2-space indent**, trailing commas where valid.
- **British English** in code, comments, and identifiers — mirrors the Python rule
  (`optimise`, `analyse`, `summarise`). Don't introduce `-ize` spellings.
- **No `any`** unless genuinely unavoidable. If you reach for it, leave a comment
  explaining why.

---

## `interface` vs `type`

- **`interface`** for object shapes (`Listing`, props, return shapes).
- **`type`** for unions, intersections, and aliases (`Agency = 'agency_a' | 'agency_b'`,
  string literal unions, mapped types).

Both work for objects, but splitting them this way makes the intent legible at a glance.

---

## Domain shapes mirror `scraper/models.py`

The Python scraper writes the DB; the frontend reads it. Shared shapes (`Listing`,
`Agency`) live in `frontend/src/types.ts` and are **hand-mirrored** from
`scraper/src/scraper/models.py`. When `models.py` changes, update `types.ts` in the
same PR.

We don't use `supabase gen types` — it pays off for many tables / churning schemas,
but for one table the verbose `Database['public']['Tables']['listings']['Row']` form
is worse than a hand-written interface.

---

## Database column names

Keep DB columns as **snake_case** in TS types (`image_url`, `last_seen`). Supabase
returns them snake_case over the wire — renaming to camelCase means a transform
layer for no real benefit. Treat the type as a description of the wire shape.

---

## Nullability — `null`, not `undefined`

Supabase returns SQL `NULL` as JS `null` (not `undefined`). Type nullable columns
as `string | null` so the type matches the runtime value. `string | null` and
`string | undefined` are different types in TS — they're not interchangeable.

---

## Money

Prices are stored as **pence** (`int4` in Postgres), typed as `number` in TS. Don't
introduce a branded `Pence` type — the ceremony isn't worth it for a single money
field. Centralise the "this is pence" knowledge in `src/lib/format.ts::formatPrice`.

---

## Dates from Supabase

Postgres `timestamptz` comes over JSON as an **ISO 8601 string**, not a `Date`
object. Type as `string` in domain types. Parse with `new Date(value)` at the
point you actually need date arithmetic or formatting — don't pre-parse on
fetch.

---

## Env vars

Frontend env vars must be prefixed `VITE_` (Vite only exposes those to the client
bundle). Declare each one in `src/vite-env.d.ts` so `import.meta.env.VITE_FOO` is
typed as `string` rather than `any`.
