# Prompt Log

A running log of every prompt Seth gives Claude on this project, in order. Newest entries at the bottom.

---

## 2026-06-29 — #1: Project kickoff & backend question

> I want this app to be a recipe deblogger. All recipe websites nowadays are full of unnecessary blog writing and FULL of ads. I want this app to webscrape recipe sites like this, get only the recipe (ingredients/instructions) and repost it onto this site in a clean and easy to read way. I want the frontend to be react in typescript, which i already created in the ui folder. I need a backend for the webscraper and perhaps some sort of machine learning model to figure out where on the site the exact recipe is. What should I do for the backend? Notice I also created an md folder. I want you to keep track of all prompts I give you and anything else important for claude in the md folder.

**What Claude did:** Inspected repo structure. Recommended Python + FastAPI; Seth
confirmed. Scaffolded the full backend under `backend/` (FastAPI app, tiered
extractor, Pydantic models, venv + installed deps). Verified extraction and server
work end-to-end. Created this prompt log and [CONTEXT.md](CONTEXT.md).

---

## 2026-06-29 — #2: HTTP client choice

> are we using python's requests or Nodes axios to send the http requests?

**What Claude did:** Clarified the backend uses `httpx` (async, requests-like) — not
`requests` (sync) or `axios` (Node). Explained the async fit with FastAPI.

---

## 2026-06-29 — #3: Anti-bot fetching strategy

> for requests to allrecipes, or maybe all sites, have python replace default library signatures with a real modern browser string, or use a full header set, or replicate devtools. Could also use curl_cffi, cloudscraper. Decide which of these is the best and let me know

**What Claude did:** Recommended `curl_cffi` (TLS/JA3 impersonation) + full header set;
explained why header-only and `cloudscraper` are insufficient. On approval, implemented
it as a fallback in `app/extractor.py`: full `BROWSER_HEADERS` always, `httpx` fast
path, `curl_cffi impersonate="chrome"` on blocked statuses, `FetchError` → 502 if both
fail. Verified allrecipes now extracts cleanly. See [CONTEXT.md](CONTEXT.md) anti-bot
section.

---

## 2026-06-29 — #4: Hook up the frontend (bare bones)

> Skip the LLM fallback, for now. Id love to get it hooked up to the front end. Make something super bare bones, no styling unless necessary.

**What Claude did:** Replaced the stock Vite template `src/App.tsx` with a minimal
recipe deblogger: URL input + "Deblog" button → `POST http://localhost:8000/extract`,
renders title/image/ingredients/instructions/source, with loading + error states.
Replaced the template `src/index.css` with a tiny reset (template forced a fixed
1126px centered layout). Verified CORS from the Vite origin and a clean typecheck
(`tsc -b`). LLM fallback explicitly deferred.

---

## 2026-06-29 — #5: WordPress WPRM HTML support

> can we add functionality for sites that use the wordpress wprm html?
>
> (also tried `/plugin marketplace add DietrichGebert/ponytail` — `/plugin` isn't
> available in this environment, so nothing was installed.)

**What Claude did:** Added a third extraction tier `_try_wprm_html` in
`app/extractor.py` — parses WP Recipe Maker markup via BeautifulSoup using the stable
`.wprm-recipe-*` classes (name, ingredient amount/unit/name/notes, instruction-text,
servings, image with data-src lazy-load, hour+minute time normalized to minutes).
Runs after recipe-scrapers + JSON-LD (most WPRM sites already emit JSON-LD; this
covers ones with missing/broken structured data). Returns `extracted_via="wprm-html"`.
Verified with fixtures; non-WPRM pages correctly return None.

---

## 2026-06-29 — #6: natashaskitchen.com returns 422

> i just tried https://natashaskitchen.com/smashed-sweet-potatoes/, which uses wprm-recipe-container from wordpress. 422 Unprocessable Content. Why is it not working?

**Root cause:** the site serves a degraded ~99KB decoy page (no recipe, no JSON-LD)
with an HTTP **200** to non-browser TLS fingerprints. Our anti-bot fallback only
triggered on error statuses (403/etc.), so it never fired — all tiers found nothing →
422. `curl_cffi` impersonation gets the real 624KB page with the recipe.

**Fix:** added a content-based fallback in `extract_recipe` — if the fast httpx page
yields no recipe, re-fetch with `curl_cffi` and re-run the tiers before giving up
(refactored tiers into `_extract_from_html`). Verified: natashaskitchen now extracts
(12 ingredients, 6 steps, via recipe-scrapers). Also confirmed the `425°F` "�" was
only the Windows console code page, not corrupted data (`'°' in text` is True).

---

## 2026-06-30 — #7: Database / saved-recipes feature (+ ponytail plugin?)

> Next, I want to add a database feature, so each recipe that is deblogged is kept and stored to view again. There might be a different page on the website that sorts them somehow. Can you outline the best way to go about this? Also, can you confirm that you are using the ponytail plugin?

**Ponytail:** Confirmed NOT used. The earlier `/plugin marketplace add
DietrichGebert/ponytail` failed ("/plugin isn't available in this environment"); no
such plugin is loaded and Claude has no knowledge of it. Did not falsely confirm.

**DB feature:** Outlined SQLite + SQLModel approach; Seth chose **auto-save** every
deblog + **alphabetical sort** + **search by title**. Implemented:
- Backend: `app/db.py` (SQLite engine, `StoredRecipe` table, `upsert_recipe`,
  `list_recipes`), startup `init_db()`, `POST /extract` now auto-saves (dedup by URL)
  and returns the stored row; added `GET /recipes?q=&sort=`, `GET /recipes/{id}`,
  `DELETE /recipes/{id}`. Added `sqlmodel` dep; `*.db` gitignored.
- Frontend: added `react-router-dom`; refactored into `api.ts`, shared `RecipeView`,
  and pages DeblogPage `/`, SavedPage `/saved` (live title search → alphabetical),
  RecipeDetailPage `/recipe/:id`.
- Verified: backend dedup + search + list endpoints all pass; frontend `tsc -b` +
  `npm run build` clean.

---

## 2026-07-01 — #8: Session-continuity CLAUDE.md

Context: Seth installed the "ponytail" plugin mid-session (not active until a new
session is started — plugins load at startup). He asked whether restarting to a new
chat would keep progress via the md files, and what he'd be missing. Gaps identified:
no git history, some verbal nuance uncaptured, and no guarantee a new session reads the
md files. He chose to fix the last one.

> just #1 please

**What Claude did:** Created root `CLAUDE.md` (auto-loaded at session start) directing
any new session to read `md/CONTEXT.md` + `md/PROMPTS.md` first, restating the standing
"keep these files maintained" request, plus a one-line project summary. (Declined
option #2, `git init`, for now.)

---

## 2026-07-01 — #9: Root README

> can you make a readme on the root directory explaining how to run the app locally

**What Claude did:** Added root `README.md` — prereqs + two-terminal run steps
(backend uvicorn, frontend vite), links to `backend/README.md` for API detail.

---

## 2026-07-02 — #10: Session setup (ponytail active)

> hello, can you confirm you are using the ponytail plugin in this session?
> for this session, take into account CONTEXT.md and PROMPTS.md and continue adding to those throughout this session

**What Claude did:** Confirmed ponytail plugin is now active (full mode) via the
session startup hook — first session where it's actually loaded (installed 07-01, took
effect on restart). Read `md/CONTEXT.md` + `md/PROMPTS.md`; will keep both maintained
this session per the standing request.

---

## 2026-07-02 — #11: Page styling

> i want to work on the styling for the page. do we use a styling library or bootsrapper or should we just use vanilla css

**What Claude did:** Recommended **vanilla CSS** (no Bootstrap/Tailwind/MUI — a styling
lib is overkill for a 3-page app; modern CSS + one stylesheet covers it). Seth chose a
**warm / recipe-card** look. Rewrote `src/index.css` as a themed stylesheet: `:root`
design tokens (cream bg, terracotta accent, serif headings), element selectors on the
existing semantic markup (`article` styled as the card). Swapped the three inline red
error styles for a `.error` class. Verified `npm run build` clean.

---

## 2026-07-06 — #12: Instagram recipe support (feasibility)

> sometimes people post recipes on their instagram... would there be a way to make it so
> people could put in an instagram link and you could display the recipe?

**What Claude did:** Scoping only (Seth: "not now, just scoping"). Assessed feasibility:
Instagram is hostile to scraping (auth-gated, no JSON-LD, ToS issues) — pragmatic fetch
tool is `yt-dlp`. Caption-based recipes are tractable and reduce to the existing tier-3
LLM TODO; video-only recipes need transcription (Whisper) + vision, a much bigger lift.
Recommended building the general LLM fallback tier first, then an IG-caption adapter on
top. Recorded the full analysis in CONTEXT.md ("Instagram recipes" section) and linked
it from Next steps. No code written.

---

## 2026-07-08 — #13: Hook up Postgres on Render

> is this app using postgres yet or still just the recipes.db file?
> i have deployed this backend to render for my live website. How would I hook up
> postgres to do my database?

**What Claude did:** Confirmed it was still SQLite. Made `app/db.py` read `DATABASE_URL`
from env (falls back to local SQLite), normalize Render's `postgres://` scheme to
`postgresql+psycopg://`, and pass `check_same_thread` only for SQLite. Added
`psycopg[binary]>=3.2` to `requirements.txt`. Gave Render steps: create a Render Postgres
in the same region, set the web service's `DATABASE_URL` to the Internal URL; table
auto-creates via `init_db()`. Verified SQLite fallback still builds cleanly. Noted old
`recipes.db` data doesn't migrate (was ephemeral on Render anyway).

---

## 2026-07-08 — #14: Footer, centered header, nav polish, intro blurb

> for the UI, can you create a footer that links to the github repo and also a tipjar.
> add icons for both. also, center "recipe deblogger" and the page menus, maybe even
> spice the menu up a bit. on the deblog page write a small excerpt on why we made this
> site.

**What Claude did:** Restructured `App.tsx` into `.app` > header/main/footer (flex
column, footer pinned to bottom). Centered the title + nav. Nav links are now pill
buttons with hover + active-page highlight (switched `Link`→`NavLink`). Added a footer
with GitHub + Tip jar links, icons via `<use href="/icons.svg#...">` — reused the
existing `github-icon`, added a heart `tipjar-icon` to the sprite. Added an intro blurb
to DeblogPage. `REPO_URL`/`TIPJAR_URL` in App.tsx are **placeholders** for Seth to fill
in. All styling in `index.css` (vanilla). Build clean.
