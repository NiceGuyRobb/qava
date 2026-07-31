from __future__ import annotations

import json
from pathlib import Path

from httpx import AsyncClient

from qava.main import create_app


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_committed_contract() -> dict:
    path = _repo_root() / "openapi" / "qava.openapi.json"
    assert path.exists(), f"openapi/qava.openapi.json not found at {path} — run 'qava openapi export' first"
    return json.loads(path.read_text(encoding="utf-8"))


def test_openapi_contract_equals_runtime() -> None:
    """SC-004 / FR-014: committed artifact must equal runtime OpenAPI exactly."""
    committed = _load_committed_contract()
    runtime = create_app().openapi()

    # Compare the full document
    assert committed == runtime, (
        "OpenAPI contract diverged from runtime. Re-run: "
        "uv run --project backend python -m qava openapi export --output openapi/qava.openapi.json"
    )


def test_openapi_export_command_writes_document(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from qava.cli import app as cli_app

    runner = CliRunner()
    output = tmp_path / "generated.openapi.json"
    result = runner.invoke(cli_app, ["openapi", "export", "--output", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()

    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["openapi"].startswith("3.")
    assert exported["info"]["title"] == "Qava MVP API"
    assert "paths" in exported
    assert "components" in exported


async def test_problem_detail_shapes_conform() -> None:
    """FR-013: every non-2xx response body must conform to ProblemDetail shape."""
    import json as _json

    from qava.api import dependencies as dep
    from qava.infrastructure.database.migrate import run_alembic_upgrade
    from qava.infrastructure.database.session import (
        DatabaseSessionManager,
        create_engine,
        create_session_factory,
    )

    class _Mgr(DatabaseSessionManager):
        def __init__(self) -> None:
            self._engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
            self._session_factory = create_session_factory(self._engine)

        async def initialize(self) -> None:
            async with self._engine.begin() as conn:
                await conn.run_sync(run_alembic_upgrade)

    mgr = _Mgr()
    await mgr.initialize()
    original = dep._db_manager
    dep.set_db_manager(mgr)

    try:
        identity = _json.dumps({"actor_id": "a1", "roles": ["author"]})
        respondent = _json.dumps({"actor_id": "r1", "roles": ["respondent"]})

        bad_payloads = [
            # These produce our custom problem responses (not FastAPI's default 422)
            ("POST", "/api/v1/questionnaire-drafts", {"id": "", "title": "", "output_contract": {}},
             {"X-Qava-Identity": identity}),
            ("GET", "/api/v1/sessions/nonexistent", {}, {"X-Qava-Identity": respondent}),
        ]

        import httpx
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app()),
            base_url="http://test",
        ) as ac:
            for method, path, body, headers in bad_payloads:
                resp = await ac.request(method, path, json=body, headers=headers)
                if resp.status_code < 400:
                    continue
                data = resp.json()
                # Problem details may be at root or nested under 'detail' (HTTPException)
                problem = data if "type" in data else data.get("detail", data)
                for key in ("type", "title", "detail", "status"):
                    assert key in problem, f"{method} {path} response missing {key!r}: {data}"
    finally:
        dep.set_db_manager(original)
        await mgr.dispose()
