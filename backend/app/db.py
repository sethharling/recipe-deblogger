"""Database setup via SQLModel.
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .models import Recipe

DATABASE_URL = "sqlite:///./recipes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StoredRecipe(SQLModel, table=True):
    """A deblogged recipe persisted to the DB.

    Mirrors the extractor's `Recipe` contract plus `id` and `created_at`.
    Ingredients/instructions are stored as JSON since we always read a recipe whole.
    """

    __tablename__ = "recipes"

    id: int | None = Field(default=None, primary_key=True)
    source_url: str = Field(unique=True, index=True)
    title: str | None = Field(default=None, index=True)
    ingredients: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    instructions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    image: str | None = None
    total_time: str | None = None
    yields: str | None = None
    extracted_via: str
    created_at: datetime = Field(default_factory=_utcnow)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


# Stored fields that get refreshed when re-deblogging an existing URL.
_REFRESHABLE = (
    "title",
    "ingredients",
    "instructions",
    "image",
    "total_time",
    "yields",
    "extracted_via",
)


def upsert_recipe(session: Session, recipe: Recipe) -> StoredRecipe:
    """Save a freshly extracted recipe, deduped by source_url.

    Re-deblogging a known URL refreshes its content but keeps its id/created_at.
    """
    existing = session.exec(
        select(StoredRecipe).where(StoredRecipe.source_url == recipe.source_url)
    ).first()

    if existing is None:
        record = StoredRecipe(**recipe.model_dump())
        session.add(record)
    else:
        for field in _REFRESHABLE:
            setattr(existing, field, getattr(recipe, field))
        record = existing
        session.add(record)

    session.commit()
    session.refresh(record)
    return record


def list_recipes(
    session: Session, *, q: str | None = None, sort: str = "title"
) -> list[StoredRecipe]:
    """List saved recipes, optional title search and sort (title|newest)."""
    statement = select(StoredRecipe)
    if q:
        statement = statement.where(StoredRecipe.title.ilike(f"%{q}%"))
    if sort == "newest":
        statement = statement.order_by(StoredRecipe.created_at.desc())
    else:  # default: alphabetical by title
        statement = statement.order_by(StoredRecipe.title)
    return list(session.exec(statement).all())
