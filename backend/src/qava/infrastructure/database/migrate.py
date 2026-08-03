"""Database migration helpers.

Alembic is the sole schema authority. ``run_alembic_upgrade`` accepts an
existing SQLAlchemy connection so file databases and in-memory test databases
run identical revisions without a second connection or a nested event loop.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_alembic_upgrade(connection: Any) -> None:
    """Apply all pending Alembic migrations on an existing sync connection.

    Pass a ``sqlalchemy.engine.Connection`` obtained from
    ``async_engine.sync_engine.connect()`` or via ``run_sync`` inside an
    async context::

        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_upgrade)
    """
    import alembic.command
    import alembic.config

    backend_root = Path(__file__).parents[4]
    cfg = alembic.config.Config()
    cfg.set_main_option("script_location", str(backend_root / "migrations"))
    cfg.set_main_option("version_path_separator", "os")
    # Tell Alembic to use the connection we supply, not the URL in alembic.ini
    cfg.attributes["connection"] = connection
    alembic.command.upgrade(cfg, "head")

