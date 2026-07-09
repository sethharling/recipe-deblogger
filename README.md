# Recipe Deblogger

[recipe-deblogger.com](https://recipe-deblogger.com)

Scrapes a recipe URL, strips the blog/ad bloat, and shows + stores just the ingredients
and instructions. Python + FastAPI backend, Vite + React + TS frontend.

## Prerequisites

- Python 3.13+
- Node.js 18+

## Run locally (two terminals)

**Terminal 1 — backend** (http://localhost:8000)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

First run creates `recipes.db` (SQLite) automatically.

**Terminal 2 — frontend** (http://localhost:5173)

```powershell
cd ui/recipe-deblogger
npm install
npm run dev
```

Open http://localhost:5173, paste a recipe URL, and hit **Deblog**. Saved recipes are
under the **Saved** tab.

More backend detail (API endpoints, extraction tiers): [backend/README.md](backend/README.md).
