from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.db.base import Base

# Импорт моделей обязателен для регистрации metadata.
from app.models import Payment, Tariff  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def get_sync_database_url() -> str:
    """Преобразует async URL в sync URL для Alembic."""

    return (
        settings.database_url
        .replace("+aiosqlite", "")
        .replace("+asyncpg", "")
    )


def run_migrations_offline() -> None:
    """Запускает миграции в offline режиме."""

    context.configure(
        url=get_sync_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запускает миграции в online режиме."""

    configuration = config.get_section(
        config.config_ini_section
    )

    if configuration is None:
        configuration = {}

    configuration["sqlalchemy.url"] = (
        get_sync_database_url()
    )

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
