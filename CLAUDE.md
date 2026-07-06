# Recipe Deblogger

**Before doing anything, read [`md/CONTEXT.md`](md/CONTEXT.md) and
[`md/PROMPTS.md`](md/PROMPTS.md).** They are the durable project memory:

- `md/CONTEXT.md` — architecture, tech decisions (and the *why*), current state, and
  the running "Next steps" list. Read this first.
- `md/PROMPTS.md` — chronological log of every prompt the user (Seth) has given, with a
  summary of what was done for each.

## Maintain these files

Keep both files up to date as work continues — this is an explicit, standing request
from Seth:

- Append every new prompt Seth gives to `md/PROMPTS.md` (newest at the bottom), with a
  short "What Claude did" note.
- Update `md/CONTEXT.md` whenever architecture, decisions, or the "Next steps" change.

## One-line summary

Web app that scrapes a recipe URL, strips the blog/ad bloat, and shows/stores just the
ingredients + instructions. Frontend: Vite + React + TS (`ui/recipe-deblogger/`).
Backend: Python + FastAPI (`backend/`). See `md/CONTEXT.md` for everything else.
