from fastapi.testclient import TestClient

from qava.main import create_app


def test_application_starts() -> None:
    """Verify the FastAPI app can start and serve its OpenAPI document."""
    from qava.api import dependencies
    from qava.infrastructure.database.migrate import run_alembic_upgrade
    from qava.infrastructure.database.session import (
        DatabaseSessionManager,
        create_engine,
        create_session_factory,
    )

    class _TestManager(DatabaseSessionManager):
        def __init__(self) -> None:
            self._engine = create_engine("sqlite+aiosqlite:///:memory:")
            self._session_factory = create_session_factory(self._engine)

        async def initialize(self) -> None:
            async with self._engine.begin() as conn:
                await conn.run_sync(run_alembic_upgrade)

    manager = _TestManager()
    original = dependencies._db_manager
    dependencies.set_db_manager(manager)

    try:
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/openapi.json")
    finally:
        dependencies.set_db_manager(original)

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Qava MVP API"
