"""FastAPI entrypoint for the recipe deblogger backend.

Run locally:
    uvicorn app.main:app --reload --port 8000

Interactive API docs: http://localhost:8000/docs
"""
from __future__ import annotations

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .db import (
    StoredRecipe,
    get_session,
    init_db,
    list_recipes,
    upsert_recipe,
)
from .extractor import FetchError, extract_recipe
from .models import ExtractRequest

app = FastAPI(title="Recipe Deblogger API", version="0.1.0")

# Vite dev server defaults to :5173. Tighten this for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", 
                   "http://recipe-deblogger.com", 
                   "https://recipe-deblogger.onrender.com/*"
                   ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()

@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract", response_model=StoredRecipe)
async def extract(
    req: ExtractRequest, session: Session = Depends(get_session)
) -> StoredRecipe:
    url = str(req.url)
    try:
        recipe = await extract_recipe(url)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Source site returned {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch URL: {exc}") from exc
    except FetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if recipe is None:
        raise HTTPException(
            status_code=422,
            detail="No recipe found on that page (no structured data). "
            "An LLM fallback is planned for pages like this.",
        )

    # Auto-save every successful deblog (deduped by source_url).
    return upsert_recipe(session, recipe)


@app.get("/recipes", response_model=list[StoredRecipe])
def get_recipes(
    q: str | None = None,
    sort: str = "title",
    session: Session = Depends(get_session),
) -> list[StoredRecipe]:
    return list_recipes(session, q=q, sort=sort)


@app.get("/recipes/{recipe_id}", response_model=StoredRecipe)
def get_recipe(
    recipe_id: int, session: Session = Depends(get_session)
) -> StoredRecipe:
    record = session.get(StoredRecipe, recipe_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return record


@app.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(
    recipe_id: int, session: Session = Depends(get_session)
) -> None:
    record = session.get(StoredRecipe, recipe_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    session.delete(record)
    session.commit()
