"""Alembic environment supporting async PostgreSQL connections."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings
from backend.app.storage.postgres import Base, normalize_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Resolve the configured database URL without logging credentials."""
    settings = get_settings()
    db_url = settings.get_database_url()
    if db_url and db_url.strip():
        return normalize_database_url(db_url)

    raw_config_url = config.get_main_option("sqlalchemy.url")
    if raw_config_url and not raw_config_url.startswith("driver://"):
        return normalize_database_url(raw_config_url)
    return normalize_database_url("sqlite:///contextshield.db")


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run synchronous Alembic operations through an async connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run Alembic through ``run_sync``."""
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations online using the async SQLAlchemy driver."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
