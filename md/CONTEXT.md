# Recipe Deblogger — Project Context for Claude

This file is the durable memory for the project. Read it at the start of any session.
The full chronological prompt history lives in [PROMPTS.md](PROMPTS.md).

## Goal

Strip the bloat (life stories, ads, pop-ups) out of recipe websites. User pastes a
recipe URL; the app fetches the page, extracts **only** the ingredients and
instructions, and reposts them in a clean, ad-free, easy-to-read layout.

## Repo layout

- `ui/recipe-deblogger/` — frontend. Vite + React 19 + TS + react-router-dom.
  - `src/api.ts` — API base + types + fetch helpers.
  - `src/RecipeView.tsx` — shared single-recipe renderer.
  - `src/pages/` — DeblogPage (`/`), SavedPage (`/saved`), RecipeDetailPage (`/recipe/:id`).
- `backend/` — Python + FastAPI. `app/main.py` (routes), `app/extractor.py` (tiered
  fetch+parse), `app/models.py` (Recipe contract), `app/db.py` (SQLite + SQLModel).
- `md/` — project docs / Claude memory (this folder).

## Key technical insight (read before building the scraper)

Most recipe sites already publish their recipe as **structured data** —
Schema.org `Recipe` JSON-LD embedded in a `<script type="application/ld+json">` tag.
This is what powers Google's recipe cards. So extraction is a tiered problem:

1. **JSON-LD / microdata parse** — works on the large majority of mainstream recipe
   sites with no ML at all. This is the primary path.
2. **Plugin-specific HTML parsing** — e.g. WP Recipe Maker (WPRM) markup. Fallback for
   sites whose structured data is missing/broken but whose HTML is well-structured.
3. **ML / LLM extraction** — last-resort fallback for messy pages. An LLM (e.g. the
   Claude API) given the stripped page text can reliably return structured
   ingredients/instructions. This replaces training a bespoke model.

Don't reach for ML first. Build the JSON-LD path, measure the miss rate, then add the
LLM fallback only for the pages that fail.

## Backend decision (2026-06-29) — CONFIRMED & SCAFFOLDED

**Python + FastAPI** (Seth confirmed). Scaffolded under `backend/`:
- `app/main.py` — FastAPI app: `GET /health`, `POST /extract`.
- `app/extractor.py` — tiered extraction (recipe-scrapers → extruct JSON-LD → WPRM HTML → [LLM TODO]).
- `app/models.py` — Pydantic API contract.
- `requirements.txt`, `README.md`, `.gitignore`, `.venv/` (created, deps installed).

Verified working: JSON-LD parse strips blog filler and returns clean
ingredients/instructions; server boots; `/extract` returns 422 for non-recipe pages.

### Stack in use
- FastAPI + uvicorn, httpx (fetch), `extruct` (JSON-LD), `recipe-scrapers` (baseline).
- LLM fallback (tier 3) NOT yet built — Anthropic SDK + stripped page text. Next big TODO.

### Anti-bot fetching (SOLVED 2026-06-29)
Big sites (allrecipes.com) returned **403** via Cloudflare-style anti-bot. Root cause:
those systems fingerprint the **TLS handshake (JA3)**, not just headers — so a perfect
header set on `httpx`/`requests` still gets flagged. Solution implemented in
`app/extractor.py`:
- Every request sends a full realistic Chrome header set (`BROWSER_HEADERS`).
- Fast path uses `httpx` (async, lightweight).
- On a blocked status (403/406/429/503) it **falls back to `curl_cffi`** with
  `impersonate="chrome"`, which replicates a real Chrome TLS fingerprint.
- If the fallback also fails it raises `FetchError` → API returns a clean 502.
- **Content-based fallback (added 2026-06-29):** some sites (natashaskitchen.com)
  serve a degraded decoy page with an HTTP *200* to non-browser TLS fingerprints, so
  status codes alone miss them. `extract_recipe` therefore retries with `curl_cffi`
  whenever the httpx page yields **no recipe** (not just on error statuses), then
  re-runs the parse tiers. Costs one extra fetch on genuine no-recipe pages.

Verified: allrecipes went 403 → clean extraction (11 ingredients, 9 steps), both
directly and through the live `POST /extract` endpoint.

Evaluated and rejected: `cloudscraper` (ineffective vs modern Cloudflare, still a
Python TLS fingerprint), header-only/devtools-copy (doesn't address TLS). Real ceiling
remains a headless browser (Playwright) for sites with active JS challenges — only add
if curl_cffi stops being enough.

### Frontend (DONE 2026-06-29)
`ui/recipe-deblogger/src/App.tsx` — bare-bones UI: URL input + "Deblog" button posts to
`http://localhost:8000/extract` (`API_BASE` const), renders title/image/ingredients/
instructions/source with loading + error states. `src/index.css` replaced with a tiny
reset (the Vite template's fixed 1126px centered layout was removed). No styling beyond
that, per Seth's request. `App.css` + template assets (hero.png etc.) are now orphaned
but harmless.

### Styling (DONE 2026-07-02)
Warm / recipe-card theme. **Vanilla CSS, no library** (decided vs Bootstrap/Tailwind/MUI
— overkill for a 3-page app; modern CSS + one stylesheet does it). All styles live in
`src/index.css`: design tokens as `:root` custom properties (cream bg, terracotta
accent, serif headings via `--serif`), element selectors on the existing semantic markup
(`main`, `nav`, `form`, `article` = the card, `article h2/h3`, etc.). Only component
change: the three inline `style={{color:'red'}}` error messages now use a `.error` class.
Build clean (`npm run build`).

### Database / saved recipes (DONE 2026-06-30)
- **SQLite (dev) / Postgres (prod) via SQLModel.** `app/db.py` reads the `DATABASE_URL`
  env var, falling back to the local file `backend/recipes.db` (gitignored) when unset.
  Models/queries identical for both. (2026-07-08: made the swap env-var driven — see
  "Postgres on Render" below.)
- One `recipes` table (`StoredRecipe`): id, unique `source_url`, title (indexed),
  ingredients/instructions as **JSON columns**, image, total_time, yields,
  extracted_via, created_at. Table auto-created on FastAPI startup.
- **Auto-save**: `POST /extract` upserts every successful deblog, deduped by
  `source_url` (re-deblog refreshes content, keeps id/created_at). Now returns the
  stored row incl. `id` + `created_at`.
- New endpoints: `GET /recipes?q=&sort=title|newest`, `GET /recipes/{id}`,
  `DELETE /recipes/{id}`. Default sort = alphabetical by title; `q` = title search
  (ILIKE). (Per Seth's choice: auto-save + alphabetical + search by title.)
- Frontend: added `react-router-dom`; `/` deblog, `/saved` (live title search →
  alphabetical list), `/recipe/:id` detail. `RecipeView` shared component.

### Instagram recipes (SCOPED, not built — 2026-07-06)
Idea: paste an Instagram link, get the recipe. Feasibility, tiered by effort:
- **Instagram is hostile** — no JSON-LD, auth-gated, ToS prohibits scraping; `curl_cffi`
  won't cut it. Pragmatic fetch tool = **`yt-dlp`** (pulls public post caption + video).
- **Tier 1 — recipe in the caption:** yt-dlp gets caption text → feed to the LLM
  extractor. This is essentially the existing tier-3 LLM TODO fed from a caption instead
  of page text. Modest work *once the LLM tier exists*; IG becomes a thin adapter.
- **Tier 2 — recipe spoken/shown in video:** download video → Whisper transcription
  (+ optional frame OCR) → LLM. A real project (transcription + vision infra). Deferred.
- **Tier 3 — recipe only in photo carousel:** vision OCR. Deferred.
- **Decision:** the general LLM fallback tier is the unlock for both messy pages and IG
  captions — build that first, add IG-caption adapter on top, skip video/vision until we
  see how many real IG recipes live in captions vs. video.

### Postgres on Render (DONE 2026-07-08)
Backend is deployed on Render. To persist data (Render's disk is ephemeral — SQLite file
was getting wiped every redeploy):
- `app/db.py` now reads `DATABASE_URL` (env), normalizes Render's `postgres://` →
  `postgresql+psycopg://`, and only passes SQLite's `check_same_thread` for sqlite URLs.
- Added `psycopg[binary]>=3.2` to `requirements.txt`.
- Render setup: create a Render Postgres (same region as the web service), set the web
  service's `DATABASE_URL` env var to the **Internal** Database URL. `init_db()`
  auto-creates the `recipes` table on startup — no migrations. Verified SQLite fallback
  still works locally.

### Next steps
1. Add the LLM fallback tier for pages without structured data (deferred by Seth 06-29).
   This also unlocks Instagram-caption support (see "Instagram recipes" above).
2. Optional polish: styling, delete button in UI, "newest" sort toggle, cook-time sort.
3. Deploy notes: BrowserRouter needs a server SPA-fallback to index.html; move
   `API_BASE` (frontend) + `DATABASE_URL`/CORS origins (backend) to env vars.

## Conventions / preferences

- Frontend: React + TypeScript.
- Keep a clean API contract between frontend and backend (e.g. `POST /extract { url }`
  returns `{ title, ingredients[], instructions[], image, sourceUrl }`).

## Legal / ethical notes to keep in mind

- Respect `robots.txt` and rate limits when scraping.
- Republishing scraped recipe text raises copyright questions (recipe *lists* aren't
  copyrightable in the US, but headnotes/photos are). Attribute and link the source.
