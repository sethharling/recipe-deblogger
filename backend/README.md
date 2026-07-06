# Recipe Deblogger — Backend

Python + FastAPI service that fetches a recipe URL and returns clean structured
ingredients/instructions. Design notes live in [../md/CONTEXT.md](../md/CONTEXT.md).

## Setup (Windows / PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/health
- Interactive docs: http://localhost:8000/docs

## API

```
POST /extract
  body: { "url": "https://some-recipe-site.com/recipe" }
  200:  { title, ingredients[], instructions[], image, total_time, yields, source_url, extracted_via }
  422:  no recipe / structured data found on the page
  502:  could not fetch the source URL
```

## Extraction tiers

1. `recipe-scrapers` — parsers for hundreds of sites + generic JSON-LD wildcard.
2. `extruct` JSON-LD — raw Schema.org `Recipe` parsing.
3. LLM fallback (planned) — Claude API on stripped page text for messy pages.

See [app/extractor.py](app/extractor.py).
