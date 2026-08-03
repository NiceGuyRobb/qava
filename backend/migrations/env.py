"""Alembic environment configuration for Qava migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config

if database_url := os.getenv("QAVA_DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # If a pre-supplied connection was injected (e.g. from run_alembic_upgrade),
    # use it directly instead of creating a new engine.
    pre_supplied = config.attributes.get("connection")
    if pre_supplied is not None:
        do_run_migrations(pre_supplied)
        return

    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        raise ValueError("Alembic sqlalchemy.url is required.")
    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    # If a pre-supplied connection was injected (e.g. from run_alembic_upgrade),
    # use it directly without creating a new event loop — safe inside pytest-asyncio.
    pre_supplied = config.attributes.get("connection")
    if pre_supplied is not None:
        do_run_migrations(pre_supplied)
        return

    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
