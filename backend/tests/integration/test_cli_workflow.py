from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qava.cli import app


def _definition_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "data"
        / "definitions"
        / "custom-home-intake"
        / "v1"
        / "definition.json"
    )


def test_publish_definition_and_create_session(tmp_path: Path) -> None:
    runner = CliRunner()
    environment = {
        "QAVA_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'qava.db'}",
    }

    publish = runner.invoke(
        app,
        ["definitions", "publish", str(_definition_path())],
        env=environment,
    )

    assert publish.exit_code == 0, publish.output
    published = json.loads(publish.output)
    assert published == {
        "questionnaire_id": "custom-home-intake",
        "version": 1,
    }

    create = runner.invoke(
        app,
        [
            "sessions",
            "create",
            "--questionnaire",
            "custom-home-intake",
            "--version",
            "1",
        ],
        env=environment,
    )

    assert create.exit_code == 0, create.output
    created = json.loads(create.output)
    assert created["session"]["id"]
    assert created["session"]["questionnaire_id"] == "custom-home-intake"
    assert created["session"]["questionnaire_version"] == 1
    assert created["session"]["revision"] == 1
    assert created["current_interaction"]["id"]


def test_create_session_reports_missing_questionnaire(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "sessions",
            "create",
            "--questionnaire",
            "missing",
            "--version",
            "1",
        ],
        env={
            "QAVA_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'qava.db'}",
        },
    )

    assert result.exit_code == 1
    assert "Questionnaire 'missing' version 1 was not found." in result.output
