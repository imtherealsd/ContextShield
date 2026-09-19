from logging.config import fileConfig
import os
from sqlalchemy import pool, create_engine
from alembic import context

from backend.app.core.config import get_settings
from backend.app.storage.postgres import Base, AuditTelemetryModel  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Dynamically resolve database connection URL from settings or environment."""
    settings = get_settings()
    db_url = settings.get_database_url() or os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return db_url
    raw_cfg = config.get_main_option("sqlalchemy.url")
    if raw_cfg and not raw_cfg.startswith("driver://"):
        return raw_cfg
    return "sqlite:///contextshield.db"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()
    # Create engine directly from resolved URL
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
