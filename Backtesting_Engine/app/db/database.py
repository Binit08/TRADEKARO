import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# Retrieve DB URL: prioritize DATABASE_URL, then SUPABASE_DB_URL, fallback to local
DB_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "SUPABASE_DB_URL",
        "postgresql://postgres:postgres@localhost:5432/postgres",
    ),
)

# Convert to async driver scheme
if DB_URL.startswith("postgresql://"):
    DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    engine = create_async_engine(
        DB_URL,
        echo=False,
        pool_pre_ping=True,  # Important for Supabase/PgBouncer to detect closed connections
        pool_size=20,
        max_overflow=20,
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    )
    
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
except Exception as e:
    logger.error(f"Failed to create async DB engine: {e}")
    raise RuntimeError("Database connection could not be established. Check DATABASE_URL or SUPABASE_DB_URL.") from e

# Session factory
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base model class
Base = declarative_base()

async def get_db():
    """Dependency for providing a transactional async session."""
    async with AsyncSessionLocal() as session:
        yield session
