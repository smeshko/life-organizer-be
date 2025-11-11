"""Database session management and engine configuration."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from life_organizer.config import get_settings

# Get settings instance
settings = get_settings()

# Create async engine with connection pooling
# pool_size=5: Maximum number of connections to keep in the pool
# max_overflow=10: Maximum number of connections that can be created beyond pool_size
# pool_pre_ping=True: Verify connections are alive before using them
# pool_recycle=3600: Recycle connections after 1 hour to avoid stale connections
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,  # Log SQL statements in debug mode
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
# expire_on_commit=False: Don't expire objects after commit (better for async)
# This factory will be used to create new database sessions
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Database session dependency for FastAPI endpoints.

    Provides an async database session that automatically handles commits
    and rollbacks. Use this as a FastAPI dependency to inject database
    sessions into your route handlers.

    Yields:
        AsyncSession: Database session for executing queries

    Example:
        @router.post("/items")
        async def create_item(
            item: ItemCreate,
            db: AsyncSession = Depends(get_db)
        ):
            new_item = Item(**item.dict())
            db.add(new_item)
            await db.commit()
            await db.refresh(new_item)
            return new_item
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
