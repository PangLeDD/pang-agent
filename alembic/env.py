import os
import sys
from logging.config import fileConfig

# Ensure the project root is on sys.path so Alembic can import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — register all ORM mappings with Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def migration_url() -> str:
    # Alembic runs synchronously here, so strip SQLAlchemy's asyncpg driver.
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _include_object(obj, name, type_, reflected, compare_to):
    # Only track tables present in our metadata; ignore LangGraph checkpoints etc.
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=migration_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=_include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = migration_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=_include_object)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
