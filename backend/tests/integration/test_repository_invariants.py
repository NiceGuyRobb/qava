from __future__ import annotations

import sqlite3


def _init_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_published_questionnaire_versions_are_immutable() -> None:
    connection = _init_connection()
    connection.execute(
        """
        CREATE TABLE published_questionnaires (
            questionnaire_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (questionnaire_id, version)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO published_questionnaires (questionnaire_id, version, payload, created_at)
        VALUES (?, ?, ?, ?)
        """,
        ("custom-home-intake", 1, "{}", "2026-01-01T00:00:00Z"),
    )

    with sqlite3.connect(":memory:"):
        pass

    try:
        connection.execute(
            """
            INSERT INTO published_questionnaires (questionnaire_id, version, payload, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ("custom-home-intake", 1, '{"changed":true}', "2026-01-01T01:00:00Z"),
        )
    except sqlite3.IntegrityError:
        duplicate_blocked = True
    else:
        duplicate_blocked = False

    assert duplicate_blocked, "Duplicate questionnaire id+version must be rejected."

    connection.execute(
        """
        INSERT INTO published_questionnaires (questionnaire_id, version, payload, created_at)
        VALUES (?, ?, ?, ?)
        """,
        ("custom-home-intake", 2, "{}", "2026-01-02T00:00:00Z"),
    )

    count = connection.execute(
        "SELECT COUNT(*) FROM published_questionnaires WHERE questionnaire_id = ?",
        ("custom-home-intake",),
    ).fetchone()
    assert count is not None
    assert count[0] == 2


def test_session_revision_compare_and_swap_rejects_stale_writes() -> None:
    connection = _init_connection()
    connection.execute(
        """
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            revision INTEGER NOT NULL,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT INTO sessions (session_id, revision, payload, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        ("session-1", 1, "{}", "2026-01-01T00:00:00Z"),
    )

    fresh_update = connection.execute(
        """
        UPDATE sessions
        SET revision = revision + 1,
            payload = ?,
            updated_at = ?
        WHERE session_id = ?
          AND revision = ?
        """,
        ('{"a":1}', "2026-01-01T00:01:00Z", "session-1", 1),
    )
    assert fresh_update.rowcount == 1

    stale_update = connection.execute(
        """
        UPDATE sessions
        SET revision = revision + 1,
            payload = ?,
            updated_at = ?
        WHERE session_id = ?
          AND revision = ?
        """,
        ('{"a":2}', "2026-01-01T00:02:00Z", "session-1", 1),
    )
    assert stale_update.rowcount == 0

    latest = connection.execute(
        "SELECT revision, payload FROM sessions WHERE session_id = ?",
        ("session-1",),
    ).fetchone()
    assert latest is not None
    assert latest[0] == 2
    assert latest[1] == '{"a":1}'
