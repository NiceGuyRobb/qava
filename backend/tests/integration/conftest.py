"""Shared fixtures for integration tests: in-memory SQLite database."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from qava.infrastructure.database.migrate import run_alembic_upgrade
from qava.infrastructure.database.session import (
    DatabaseSessionManager,
    create_engine,
    create_session_factory,
)


class InMemoryDatabaseSessionManager(DatabaseSessionManager):
    """Session manager that uses a shared in-memory SQLite database for tests."""

    def __init__(self) -> None:
        # Don't call super().__init__() to avoid reading Settings
        self._engine = create_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        self._session_factory = create_session_factory(self._engine)

    async def initialize(self) -> None:
        """Apply Alembic migrations to the in-memory DB via the same async engine."""
        async with self._engine.begin() as conn:
            await conn.run_sync(run_alembic_upgrade)


@pytest_asyncio.fixture
async def in_memory_manager():
    """Create a fresh in-memory SQLite DB with migrations applied."""
    manager = InMemoryDatabaseSessionManager()
    await manager.initialize()
    yield manager
    await manager.dispose()


@pytest_asyncio.fixture
async def client(in_memory_manager: InMemoryDatabaseSessionManager):
    """HTTPX AsyncClient pointing at the FastAPI app with an in-memory database."""
    from qava.api import dependencies
    from qava.main import create_app

    # Override the global DB manager with the test in-memory one
    original = dependencies._db_manager
    dependencies.set_db_manager(in_memory_manager)

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Restore
    dependencies.set_db_manager(original)
