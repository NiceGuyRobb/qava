from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml

from qava.application.authoring import AuthoringService
from qava.application.interviewing import InterviewingService
from qava.config import Settings
from qava.domain.models import QuestionnaireId
from qava.infrastructure.contracts.definition_pack import load_definition_pack
from qava.infrastructure.contracts.registry import ContractRegistry
from qava.infrastructure.database.repositories import (
    SQLiteDraftRepository,
    SQLiteInteractionRepository,
    SQLitePublishedQuestionnaireRepository,
    SQLiteSessionRepository,
)
from qava.infrastructure.database.session import DatabaseSessionManager
from qava.main import create_app

app = typer.Typer(help="Qava developer tooling")
contracts_app = typer.Typer(help="Data and schema contract commands")
openapi_app = typer.Typer(help="OpenAPI contract commands")
definitions_app = typer.Typer(help="Definition pack commands")
sessions_app = typer.Typer(help="Interview session commands")
db_app = typer.Typer(help="Database maintenance commands")
app.add_typer(contracts_app, name="contracts")
app.add_typer(openapi_app, name="openapi")
app.add_typer(definitions_app, name="definitions")
app.add_typer(sessions_app, name="sessions")
app.add_typer(db_app, name="db")
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]


@contracts_app.command("validate")
def validate_contracts(
    repo_root: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=False,
            dir_okay=True,
            help="Repository root that contains the data contracts.",
        ),
    ] = DEFAULT_REPO_ROOT,
) -> None:
    registry = ContractRegistry(repo_root=repo_root)
    issues = registry.validate_all()

    if issues:
        for issue in issues:
            typer.echo(f"ERROR {issue.location}: {issue.message}")
        raise typer.Exit(code=1)

    typer.echo(f"Validated {registry.schema_count} schemas and all contract fixtures.")


def load_openapi_contract(repo_root: Path) -> dict[str, object]:
    contract_path = repo_root / "openapi" / "qava.openapi.json"
    with contract_path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("OpenAPI contract must be a JSON object.")
    return loaded


@openapi_app.command("export")
def export_openapi(
    output: Annotated[
        Path,
        typer.Option(
            help="Output file path for exported FastAPI OpenAPI JSON.",
        ),
    ],
) -> None:
    openapi_document = create_app().openapi()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(openapi_document, indent=2, sort_keys=True), encoding="utf-8")
    typer.echo(f"Exported OpenAPI {openapi_document['info']['version']} to {output}.")


@openapi_app.command("validate")
def validate_openapi(
    repo_root: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=False,
            dir_okay=True,
            help="Repository root that contains openapi/qava.openapi.json.",
        ),
    ] = DEFAULT_REPO_ROOT,
) -> None:
    contract = load_openapi_contract(repo_root)
    runtime = create_app().openapi()

    diffs: list[str] = []
    for key in ("paths", "components", "info", "openapi"):
        c_val = contract.get(key)
        r_val = runtime.get(key)
        if c_val != r_val:
            diffs.append(f"  [{key}] contract != runtime")

    if diffs:
        for d in diffs:
            typer.echo(f"ERROR {d}")
        raise typer.Exit(code=1)

    typer.echo(f"OpenAPI contract and runtime match ({runtime.get('info', {}).get('version', '?')}).")


@definitions_app.command("publish")
def publish_definition(
    manifest: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Path to a v1 definition.json manifest.",
        ),
    ],
    published_by: Annotated[
        str,
        typer.Option(help="Actor recorded as the questionnaire publisher."),
    ] = "qava-cli-author",
) -> None:
    try:
        result = asyncio.run(_publish_definition(manifest, published_by=published_by))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(f"ERROR {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, sort_keys=True))


@definitions_app.command("bootstrap-meta")
def bootstrap_meta_questionnaire(
    published_by: Annotated[
        str,
        typer.Option(help="Actor recorded as the meta-questionnaire publisher."),
    ] = "qava-bootstrap",
) -> None:
    manifest = DEFAULT_REPO_ROOT / "data" / "definitions" / "meta" / "v1" / "definition.json"
    try:
        result = asyncio.run(_publish_definition(manifest, published_by=published_by))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(f"ERROR {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, sort_keys=True))


@sessions_app.command("create")
def create_session(
    questionnaire: Annotated[
        str,
        typer.Option(help="Published questionnaire ID."),
    ],
    version: Annotated[
        int,
        typer.Option(min=1, help="Exact published questionnaire version."),
    ],
    created_by: Annotated[
        str,
        typer.Option(help="Actor recorded as the session respondent."),
    ] = "qava-cli-respondent",
) -> None:
    result = asyncio.run(
        _create_session(
            questionnaire_id=questionnaire,
            version=version,
            created_by=created_by,
        )
    )
    if result is None:
        typer.echo(
            f"Questionnaire {questionnaire!r} version {version} was not found.",
            err=True,
        )
        raise typer.Exit(code=1)
    typer.echo(json.dumps(result, sort_keys=True))


async def _publish_definition(manifest_path: Path, *, published_by: str) -> dict[str, Any]:
    pack = load_definition_pack(manifest_path)
    manager = DatabaseSessionManager(Settings())
    await manager.initialize()
    try:
        async with manager.session() as database_session:
            drafts = SQLiteDraftRepository(database_session)
            questionnaires = SQLitePublishedQuestionnaireRepository(database_session)
            existing = await questionnaires.get(
                QuestionnaireId(pack.questionnaire_id), pack.version
            )
            if existing is not None:
                return {
                    "questionnaire_id": str(existing.questionnaire_id),
                    "version": existing.version,
                }

            latest_version = await questionnaires.get_latest_version(
                QuestionnaireId(pack.questionnaire_id)
            )
            expected_version = (latest_version or 0) + 1
            if pack.version != expected_version:
                raise ValueError(
                    f"Definition version {pack.version} cannot follow "
                    f"published version {latest_version}."
                )

            service = AuthoringService(drafts, questionnaires)
            await service.create_draft(
                draft_id=pack.questionnaire_id,
                title=pack.title,
                description=pack.description,
                output_contract=pack.output_contract,
                questions=pack.questions,
            )
            published = await service.publish_draft(
                pack.questionnaire_id, published_by=published_by
            )
            if published is None:
                raise ValueError(f"Draft {pack.questionnaire_id!r} was not persisted.")
            return {
                "questionnaire_id": str(published.questionnaire_id),
                "version": published.version,
            }
    finally:
        await manager.dispose()


async def _create_session(
    *, questionnaire_id: str, version: int, created_by: str
) -> dict[str, Any] | None:
    manager = DatabaseSessionManager(Settings())
    await manager.initialize()
    try:
        async with manager.session() as database_session:
            service = InterviewingService(
                SQLitePublishedQuestionnaireRepository(database_session),
                SQLiteSessionRepository(database_session),
                SQLiteInteractionRepository(database_session),
            )
            return await service.create_session(
                questionnaire_id=questionnaire_id,
                questionnaire_version=version,
                created_by=created_by,
            )
    finally:
        await manager.dispose()


if __name__ == "__main__":
    app()


# ---------------------------------------------------------------------------
# T027: db reconcile — stamp legacy databases created before Alembic
# ---------------------------------------------------------------------------

# Expected columns for the initial schema (0001_initial)
_EXPECTED_0001_COLUMNS: dict[str, set[str]] = {
    "questionnaire_drafts": {
        "draft_id", "base_version", "title", "description",
        "output_contract_json", "output_needs_json", "questions_json",
        "health_policy_json", "assistance_policy_json", "decisions_json",
        "validation_issues_json", "updated_at",
    },
    "published_questionnaires": {
        "questionnaire_id", "version", "schema_version", "title",
        "output_contract_json", "output_needs_json", "questions_json",
        "component_catalog_version", "health_policy_json", "assistance_policy_json",
        "allowed_result_adapters_json", "content_hash", "published_by", "published_at",
    },
    "sessions": {
        "session_id", "questionnaire_id", "questionnaire_version", "revision",
        "status", "active_topic_id", "answers_json", "generated_interactions_json",
        "created_by", "created_at", "updated_at",
    },
    "interactions": {
        "interaction_id", "session_id", "session_revision", "kind",
        "interaction_snapshot_json", "submitted_value_json", "actor_id",
        "metadata_json", "created_at",
    },
    "assistance_proposals": {
        "proposal_id", "session_id", "interaction_id", "operation", "payload_json",
        "status", "created_at",
    },
    "publication_attempts": {
        "publication_id", "session_id", "session_revision", "adapter",
        "destination", "idempotency_key", "status", "requested_by",
        "external_reference", "error_json", "created_at", "completed_at",
    },
}


@db_app.command("reconcile")
def db_reconcile(
    db_url: Annotated[
        str,
        typer.Option("--db-url", help="SQLite URL for the database to reconcile."),
    ] = "",
    stamp_old: Annotated[
        bool,
        typer.Option("--stamp-old", help="Stamp the database with 0001_initial if schema matches."),
    ] = False,
) -> None:
    """Verify a legacy database schema and optionally stamp it with 0001_initial.

    Only stamps when the exact expected columns are present. Refuses on mismatch.
    """
    import sqlite3

    if not db_url:
        db_url = str(Settings().database_url)

    # Extract path from sqlite:///path
    if ":///" in db_url:
        db_path = db_url.split("///", 1)[-1]
    else:
        typer.echo(f"ERROR Unsupported database URL: {db_url!r}", err=True)
        raise typer.Exit(code=1)

    conn = sqlite3.connect(db_path)
    try:
        # Check if alembic_version exists
        tables_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = {r[0] for r in tables_rows}

        if "alembic_version" in tables:
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
            typer.echo(f"Database already tracked at revision: {version[0] if version else 'none'}")
            return

        # Verify expected 0001 schema
        mismatches: list[str] = []
        for table, expected_cols in _EXPECTED_0001_COLUMNS.items():
            if table not in tables:
                mismatches.append(f"Missing table: {table!r}")
                continue
            actual_cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols
            if missing:
                mismatches.append(f"{table}: missing columns {sorted(missing)}")
            if extra:
                mismatches.append(f"{table}: unexpected columns {sorted(extra)}")

        if mismatches:
            for m in mismatches:
                typer.echo(f"SCHEMA MISMATCH {m}", err=True)
            raise typer.Exit(code=1)

        if not stamp_old:
            typer.echo("Schema matches 0001_initial. Re-run with --stamp-old to mark it tracked.")
            return

        conn.execute(
            "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"
        )
        conn.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)", ("0001_initial",)
        )
        conn.commit()
        typer.echo("Stamped database with revision 0001_initial.")
    finally:
        conn.close()
