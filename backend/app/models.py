"""Pydantic models defining the API contract shared with the React frontend."""
from __future__ import annotations

from pydantic import BaseModel, HttpUrl


class ExtractRequest(BaseModel):
    url: HttpUrl


class Recipe(BaseModel):
    title: str | None = None
    ingredients: list[str] = []
    instructions: list[str] = []
    image: str | None = None
    total_time: str | None = None
    yields: str | None = None
    source_url: str
    # Which extraction tier produced this result: "json-ld" | "recipe-scrapers" | "llm"
    extracted_via: str
