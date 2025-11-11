"""Database models and persistence layer.

This package provides the database infrastructure for the Life Organizer application:
- Base: SQLAlchemy declarative base for all ORM models
- engine: Async database engine for executing queries
- get_db: FastAPI dependency for injecting database sessions into routes

Example:
    from life_organizer.db import Base, get_db
    from sqlalchemy.ext.asyncio import AsyncSession
    from fastapi import Depends

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

from life_organizer.db.base import Base
from life_organizer.db.session import engine, get_db

__all__ = ["Base", "engine", "get_db"]
