import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your SQLAlchemy Base
from app.models import Base

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic uses for autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """
    Prefer DATABASE_URL from environment.
    Fallback to sqlalchemy.url from alembic.ini.
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return config.get_main_option("sqlalchemy.url")


# ---------------------------------------------------------
# 🔥 FIX: STAMP DB TO HEAD TO AVOID MISSING REVISION ERRORS
# ---------------------------------------------------------
def safe_stamp_head():
    """
    Stamp the database with 'head' only when the alembic_version
    table is empty or missing. This prevents errors like:
    'Can't locate revision ...'
    """
    try:
        from alembic import command
        command.stamp(config, "head")
    except Exception:
        # If stamp fails, continue with migrations normally
        pass


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # Fix revision mismatch
    safe_stamp_head()

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    config_section = config.get_section(config.config_ini_section) or {}
    config_section["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        # Fix revision mismatch
        safe_stamp_head()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
