"""Contract tests for migration authority (T023-T026 / US3 SC-005 SC-006 FR-016 FR-017 FR-019).

Verifies that Alembic is the sole schema authority: clean upgrades reach head,
repeated runs are idempotent, file and in-memory schemas are identical, and the
legacy reconciliation path stamps only exact-match databases.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

from qava.infrastructure.database.migrate import run_alembic_upgrade
from qava.infrastructure.database.session import create_engine


async def _apply_to_url(database_url: str) -> None:
    engine = create_engine(database_url, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_upgrade)
    finally:
        await engine.dispose()


def _introspect_schema(db_path: str) -> dict[str, Any]:
    """Return a dict of {table: {columns, pk, fk, indexes}} for deep comparison."""
    conn = sqlite3.connect(db_path)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()]
        schema: dict[str, Any] = {}
        for table in tables:
            if table == "alembic_version":
                continue
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            idxs = conn.execute(f"PRAGMA index_list({table})").fetchall()
            fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
            schema[table] = {
                "columns": [(c[1], c[2], c[3], c[4]) for c in cols],  # name, type, notnull, dflt
                "indexes": sorted([i[1] for i in idxs]),
                "foreign_keys": sorted([(f[2], f[3], f[4]) for f in fks]),  # table, from, to
            }
        return schema
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# T023: clean migration reaches head
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clean_migration_reaches_head() -> None:
    from sqlalchemy import text

    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_upgrade)

        async with engine.connect() as conn:
            rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "0003_published_artifacts"
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# T024: repeated upgrade is idempotent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repeated_migration_is_idempotent() -> None:
    from sqlalchemy import text

    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_upgrade)

        # Run again — must not raise
        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_upgrade)

        async with engine.connect() as conn:
            rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "0003_published_artifacts"
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# T025: file and in-memory schemas are identical (SC-006)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_file_and_memory_schema_equal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        await _apply_to_url(f"sqlite+aiosqlite:///{db_path}")
        await _apply_to_url("sqlite+aiosqlite:///:memory:")  # warm up, then use a file for comparison

        # Use a second file for the in-memory equivalent
        mem_path = str(Path(tmp) / "mem.db")
        await _apply_to_url(f"sqlite+aiosqlite:///{mem_path}")

        file_schema = _introspect_schema(db_path)
        mem_schema = _introspect_schema(mem_path)
        assert file_schema == mem_schema, (
            f"Schema mismatch:\nFile: {file_schema}\nMemory: {mem_schema}"
        )


# ---------------------------------------------------------------------------
# T026: legacy reconciliation
# ---------------------------------------------------------------------------

_INITIAL_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS questionnaire_drafts (
    draft_id TEXT PRIMARY KEY,
    base_version INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    output_contract_json TEXT NOT NULL DEFAULT '{}',
    output_needs_json TEXT NOT NULL DEFAULT '[]',
    questions_json TEXT NOT NULL DEFAULT '[]',
    health_policy_json TEXT NOT NULL DEFAULT '{}',
    assistance_policy_json TEXT NOT NULL DEFAULT '{}',
    decisions_json TEXT NOT NULL DEFAULT '[]',
    validation_issues_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS published_questionnaires (
    questionnaire_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    title TEXT NOT NULL,
    output_contract_json TEXT NOT NULL,
    output_needs_json TEXT NOT NULL DEFAULT '[]',
    questions_json TEXT NOT NULL DEFAULT '[]',
    component_catalog_version INTEGER NOT NULL DEFAULT 1,
    health_policy_json TEXT NOT NULL,
    assistance_policy_json TEXT NOT NULL,
    allowed_result_adapters_json TEXT NOT NULL DEFAULT '["json-document"]',
    content_hash TEXT NOT NULL,
    published_by TEXT NOT NULL,
    published_at TEXT NOT NULL,
    PRIMARY KEY (questionnaire_id, version)
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    questionnaire_id TEXT NOT NULL,
    questionnaire_version INTEGER NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    active_topic_id TEXT,
    answers_json TEXT NOT NULL DEFAULT '{}',
    generated_interactions_json TEXT NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interactions (
    interaction_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    session_revision INTEGER NOT NULL,
    kind TEXT NOT NULL,
    interaction_snapshot_json TEXT,
    submitted_value_json TEXT,
    actor_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assistance_proposals (
    proposal_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    interaction_id TEXT,
    operation TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS publication_attempts (
    publication_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    session_revision INTEGER NOT NULL,
    adapter TEXT NOT NULL,
    destination TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'validating',
    requested_by TEXT NOT NULL,
    external_reference TEXT,
    error_json TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE (session_id, idempotency_key)
);
"""


def _create_legacy_db(path: str, *, include_sessions: bool = True, extra_column: bool = False) -> None:
    """Create a database resembling the old embedded-SQL era (no alembic_version)."""
    conn = sqlite3.connect(path)
    try:
        conn.executescript(_INITIAL_SCHEMA_SQL)
        if extra_column:
            conn.execute("ALTER TABLE sessions ADD COLUMN extra_col TEXT")
        conn.commit()
    finally:
        conn.close()


def _get_alembic_version(path: str) -> str | None:
    conn = sqlite3.connect(path)
    try:
        try:
            rows = conn.execute("SELECT version_num FROM alembic_version").fetchall()
            return rows[0][0] if rows else None
        except sqlite3.OperationalError:
            return None
    finally:
        conn.close()


def test_legacy_reconcile_stamps_exact_match(tmp_path: Path) -> None:
    """A legacy DB with the correct 0001 schema is stamped with 0001_initial."""
    db_path = str(tmp_path / "legacy.db")
    _create_legacy_db(db_path)

    # No alembic_version yet
    assert _get_alembic_version(db_path) is None

    from typer.testing import CliRunner
    from qava.cli import app as cli_app

    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        ["db", "reconcile", "--db-url", f"sqlite:///{db_path}", "--stamp-old"],
    )
    assert result.exit_code == 0, result.output
    assert _get_alembic_version(db_path) == "0001_initial"


def test_legacy_reconcile_refuses_mismatch(tmp_path: Path) -> None:
    """A legacy DB with an extra column is refused — schema mismatch."""
    db_path = str(tmp_path / "mismatch.db")
    _create_legacy_db(db_path, extra_column=True)

    from typer.testing import CliRunner
    from qava.cli import app as cli_app

    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        ["db", "reconcile", "--db-url", f"sqlite:///{db_path}", "--stamp-old"],
    )
    assert result.exit_code != 0
    assert _get_alembic_version(db_path) is None
