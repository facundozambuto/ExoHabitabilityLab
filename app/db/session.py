"""
Database session management.

Provides async session factory and dependency injection for database access.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from urllib.parse import urlsplit, urlunsplit, parse_qsl

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_engine_kwargs(database_url: str) -> tuple[str, dict]:
    """
    Normalize the database URL and build engine kwargs.

    Handles Postgres (Neon / serverless) where the asyncpg driver does not
    understand libpq query params like ``sslmode``/``channel_binding`` and
    where prepared statements must be disabled when going through a pgBouncer
    pooler. On serverless we also use NullPool so connections are not reused
    across invocations.
    """
    engine_kwargs: dict = {"echo": settings.debug, "future": True}

    if database_url.startswith("postgres"):
        # Normalize scheme to the asyncpg driver.
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )

        # Strip libpq-only query params that asyncpg rejects.
        parts = urlsplit(database_url)
        query = [
            (k, v)
            for k, v in parse_qsl(parts.query)
            if k not in {"sslmode", "channel_binding"}
        ]
        from urllib.parse import urlencode

        database_url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

        engine_kwargs["poolclass"] = NullPool
        engine_kwargs["connect_args"] = {
            "ssl": True,
            # Disable prepared statement cache for pgBouncer compatibility.
            "statement_cache_size": 0,
        }

    return database_url, engine_kwargs


_database_url, _engine_kwargs = _build_engine_kwargs(settings.database_url)

# Create async engine
engine = create_async_engine(_database_url, **_engine_kwargs)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of request context.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        async with get_db_context() as db:
            result = await db.execute(query)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    Should be called on application startup.
    """
    from app.db.base import Base
    from app.models import exoplanet  # noqa: F401 - Import to register models
    
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called on application shutdown.
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")
