from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Literal, cast

from sqlalchemy import text
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from qava.domain.models import (
    AssistancePolicy,
    HealthPolicy,
    InteractionId,
    NavigationFocus,
    ProblemDetail,
    PublicationId,
    PublicationRecord,
    PublicationStatus,
    PublishedArtifactRecord,
    PublishedQuestionnaireRecord,
    QuestionnaireId,
    RuntimeInteractionRecord,
    SessionId,
    SessionRecord,
    SessionStatus,
    SkipDisposition,
)

InteractionKind = Literal[
    "question_shown",
    "answer_accepted",
    "answer_rejected",
    "skip",
    "clarification",
    "confirmation",
    "review",
    "navigation",
    "assistance_fallback",
]


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC).isoformat()
    return value.astimezone(UTC).isoformat()


def _from_utc_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _json_dump(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _json_load_object(value: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError("Expected JSON object payload.")
    return cast(dict[str, Any], loaded)


def _json_load_list(value: str) -> list[dict[str, Any]]:
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        raise ValueError("Expected JSON array payload.")
    return [cast(dict[str, Any], item) for item in loaded if isinstance(item, dict)]


class SQLiteDraftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        draft_id: str,
        payload: Mapping[str, Any],
        *,
        updated_at: datetime,
    ) -> None:
        updated_at_iso = _to_utc_iso(updated_at)

        await self._session.execute(
            text(
                """
                INSERT INTO questionnaire_drafts (
                    draft_id,
                    base_version,
                    title,
                    description,
                    output_contract_json,
                    output_needs_json,
                    questions_json,
                    health_policy_json,
                    assistance_policy_json,
                    decisions_json,
                    validation_issues_json,
                    updated_at
                )
                VALUES (
                    :draft_id,
                    NULL,
                    :title,
                    :description,
                    :output_contract_json,
                    :output_needs_json,
                    :questions_json,
                    :health_policy_json,
                    :assistance_policy_json,
                    :decisions_json,
                    :validation_issues_json,
                    :updated_at
                )
                ON CONFLICT(draft_id) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    output_contract_json = excluded.output_contract_json,
                    output_needs_json = excluded.output_needs_json,
                    questions_json = excluded.questions_json,
                    health_policy_json = excluded.health_policy_json,
                    assistance_policy_json = excluded.assistance_policy_json,
                    decisions_json = excluded.decisions_json,
                    validation_issues_json = excluded.validation_issues_json,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "draft_id": draft_id,
                "title": str(payload.get("title", "")),
                "description": payload.get("description"),
                "output_contract_json": _json_dump(payload.get("output_contract", {})),
                "output_needs_json": _json_dump(payload.get("output_needs", [])),
                "questions_json": _json_dump(payload.get("questions", [])),
                "health_policy_json": _json_dump(payload.get("health_policy", {})),
                "assistance_policy_json": _json_dump(payload.get("assistance_policy", {})),
                "decisions_json": _json_dump(payload.get("decisions", [])),
                "validation_issues_json": _json_dump(payload.get("validation_issues", [])),
                "updated_at": updated_at_iso,
            },
        )

    async def get(self, draft_id: str) -> dict[str, Any] | None:
        result = await self._session.execute(
            text(
                """
                SELECT
                    draft_id,
                    base_version,
                    title,
                    description,
                    output_contract_json,
                    output_needs_json,
                    questions_json,
                    health_policy_json,
                    assistance_policy_json,
                    decisions_json,
                    validation_issues_json,
                    updated_at
                FROM questionnaire_drafts
                WHERE draft_id = :draft_id
                """
            ),
            {"draft_id": draft_id},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return {
            "id": row["draft_id"],
            "base_version": row["base_version"],
            "title": row["title"],
            "description": row["description"],
            "output_contract": _json_load_object(cast(str, row["output_contract_json"])),
            "output_needs": _json_load_list(cast(str, row["output_needs_json"])),
            "questions": _json_load_list(cast(str, row["questions_json"])),
            "health_policy": _json_load_object(cast(str, row["health_policy_json"])),
            "assistance_policy": _json_load_object(cast(str, row["assistance_policy_json"])),
            "decisions": _json_load_list(cast(str, row["decisions_json"])),
            "validation_issues": _json_load_list(cast(str, row["validation_issues_json"])),
            "updated_at": _from_utc_iso(cast(str, row["updated_at"])),
        }

    async def delete(self, draft_id: str) -> bool:
        result = await self._session.execute(
            text("DELETE FROM questionnaire_drafts WHERE draft_id = :draft_id"),
            {"draft_id": draft_id},
        )
        return cast(CursorResult[Any], result).rowcount > 0


class SQLitePublishedQuestionnaireRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, record: PublishedQuestionnaireRecord) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO published_questionnaires (
                    questionnaire_id,
                    version,
                    schema_version,
                    title,
                    output_contract_json,
                    output_needs_json,
                    questions_json,
                    component_catalog_version,
                    health_policy_json,
                    assistance_policy_json,
                    allowed_result_adapters_json,
                    content_hash,
                    published_by,
                    published_at
                )
                VALUES (
                    :questionnaire_id,
                    :version,
                    1,
                    :title,
                    :output_contract_json,
                    :output_needs_json,
                    :questions_json,
                    1,
                    :health_policy_json,
                    :assistance_policy_json,
                    :allowed_result_adapters_json,
                    :content_hash,
                    :published_by,
                    :published_at
                )
                """
            ),
            {
                "questionnaire_id": str(record.questionnaire_id),
                "version": record.version,
                "title": record.title,
                "output_contract_json": _json_dump(record.output_contract),
                "output_needs_json": _json_dump(record.output_needs),
                "questions_json": _json_dump(record.questions),
                "health_policy_json": record.health_policy.model_dump_json(),
                "assistance_policy_json": record.assistance_policy.model_dump_json(),
                "allowed_result_adapters_json": _json_dump(["json-document"]),
                "content_hash": record.content_hash,
                "published_by": record.published_by,
                "published_at": _to_utc_iso(record.published_at),
            },
        )

    async def get(
        self,
        questionnaire_id: QuestionnaireId,
        version: int,
    ) -> PublishedQuestionnaireRecord | None:
        result = await self._session.execute(
            text(
                """
                SELECT
                    questionnaire_id,
                    version,
                    title,
                    output_contract_json,
                    output_needs_json,
                    questions_json,
                    health_policy_json,
                    assistance_policy_json,
                    content_hash,
                    published_by,
                    published_at
                FROM published_questionnaires
                WHERE questionnaire_id = :questionnaire_id
                  AND version = :version
                """
            ),
            {"questionnaire_id": str(questionnaire_id), "version": version},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return _published_row_to_record(row)

    async def get_latest_version(self, questionnaire_id: QuestionnaireId) -> int | None:
        result = await self._session.execute(
            text(
                """
                SELECT MAX(version) AS latest_version
                FROM published_questionnaires
                WHERE questionnaire_id = :questionnaire_id
                """
            ),
            {"questionnaire_id": str(questionnaire_id)},
        )
        row = result.mappings().first()
        if row is None:
            return None
        latest = row["latest_version"]
        return cast(int | None, latest)


class SQLiteSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: SessionRecord) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO sessions (
                    session_id,
                    questionnaire_id,
                    questionnaire_version,
                    revision,
                    status,
                    active_topic_id,
                    answers_json,
                    generated_interactions_json,
                    skip_dispositions_json,
                    navigation_focus_json,
                    created_by,
                    created_at,
                    updated_at
                )
                VALUES (
                    :session_id,
                    :questionnaire_id,
                    :questionnaire_version,
                    :revision,
                    :status,
                    :active_topic_id,
                    :answers_json,
                    :generated_interactions_json,
                    :skip_dispositions_json,
                    :navigation_focus_json,
                    :created_by,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "session_id": str(record.session_id),
                "questionnaire_id": str(record.questionnaire_id),
                "questionnaire_version": record.questionnaire_version,
                "revision": record.revision,
                "status": record.status,
                "active_topic_id": record.active_topic_id,
                "answers_json": _json_dump(record.answers),
                "generated_interactions_json": _json_dump(record.generated_interactions),
                "skip_dispositions_json": _json_dump(_skip_dispositions_to_dict(record.skip_dispositions)),
                "navigation_focus_json": (
                    None if record.navigation_focus is None
                    else _json_dump(_navigation_focus_to_dict(record.navigation_focus))
                ),
                "created_by": record.created_by,
                "created_at": _to_utc_iso(record.created_at),
                "updated_at": _to_utc_iso(record.updated_at),
            },
        )

    async def get(self, session_id: SessionId) -> SessionRecord | None:
        result = await self._session.execute(
            text(
                """
                SELECT
                    session_id,
                    questionnaire_id,
                    questionnaire_version,
                    revision,
                    status,
                    active_topic_id,
                    answers_json,
                    generated_interactions_json,
                    skip_dispositions_json,
                    navigation_focus_json,
                    created_by,
                    created_at,
                    updated_at
                FROM sessions
                WHERE session_id = :session_id
                """
            ),
            {"session_id": str(session_id)},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return _session_row_to_record(row)

    async def update_with_revision(
        self,
        session_id: SessionId,
        *,
        expected_revision: int,
        answers: Mapping[str, Any],
        generated_interactions: list[dict[str, Any]],
        status: SessionStatus,
        active_topic_id: str | None,
        skip_dispositions: Mapping[str, Any],
        navigation_focus: Mapping[str, Any] | None,
        updated_at: datetime,
    ) -> SessionRecord | None:
        update_result = await self._session.execute(
            text(
                """
                UPDATE sessions
                SET revision = revision + 1,
                    status = :status,
                    active_topic_id = :active_topic_id,
                    answers_json = :answers_json,
                    generated_interactions_json = :generated_interactions_json,
                    skip_dispositions_json = :skip_dispositions_json,
                    navigation_focus_json = :navigation_focus_json,
                    updated_at = :updated_at
                WHERE session_id = :session_id
                  AND revision = :expected_revision
                """
            ),
            {
                "session_id": str(session_id),
                "expected_revision": expected_revision,
                "status": status,
                "active_topic_id": active_topic_id,
                "answers_json": _json_dump(dict(answers)),
                "generated_interactions_json": _json_dump(generated_interactions),
                "skip_dispositions_json": _json_dump(dict(skip_dispositions)),
                "navigation_focus_json": (
                    None if navigation_focus is None else _json_dump(dict(navigation_focus))
                ),
                "updated_at": _to_utc_iso(updated_at),
            },
        )
        if cast(CursorResult[Any], update_result).rowcount == 0:
            return None
        return await self.get(session_id)

    async def delete(self, session_id: SessionId) -> bool:
        result = await self._session.execute(
            text("DELETE FROM sessions WHERE session_id = :session_id"),
            {"session_id": str(session_id)},
        )
        return cast(CursorResult[Any], result).rowcount > 0


class SQLiteInteractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, record: RuntimeInteractionRecord) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO interactions (
                    interaction_id,
                    session_id,
                    session_revision,
                    kind,
                    interaction_snapshot_json,
                    submitted_value_json,
                    actor_id,
                    metadata_json,
                    created_at
                )
                VALUES (
                    :interaction_id,
                    :session_id,
                    :session_revision,
                    :kind,
                    :interaction_snapshot_json,
                    :submitted_value_json,
                    :actor_id,
                    :metadata_json,
                    :created_at
                )
                """
            ),
            {
                "interaction_id": str(record.interaction_id),
                "session_id": str(record.session_id),
                "session_revision": record.session_revision,
                "kind": record.kind,
                "interaction_snapshot_json": (
                    None
                    if record.interaction_snapshot is None
                    else _json_dump(record.interaction_snapshot)
                ),
                "submitted_value_json": _json_dump(record.submitted_value),
                "actor_id": record.actor_id,
                "metadata_json": _json_dump(record.metadata),
                "created_at": _to_utc_iso(record.created_at),
            },
        )

    async def list_for_session(self, session_id: SessionId) -> list[RuntimeInteractionRecord]:
        result = await self._session.execute(
            text(
                """
                SELECT
                    interaction_id,
                    session_id,
                    session_revision,
                    kind,
                    interaction_snapshot_json,
                    submitted_value_json,
                    actor_id,
                    metadata_json,
                    created_at
                FROM interactions
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                """
            ),
            {"session_id": str(session_id)},
        )
        rows = result.mappings().all()
        return [_interaction_row_to_record(row) for row in rows]


class SQLiteAssistanceProposalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        proposal_id: str,
        *,
        session_id: SessionId,
        operation: str,
        payload: Mapping[str, Any],
        status: str,
        created_at: datetime,
        interaction_id: str | None = None,
    ) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO assistance_proposals (
                    proposal_id,
                    session_id,
                    interaction_id,
                    operation,
                    payload_json,
                    status,
                    created_at
                )
                VALUES (
                    :proposal_id,
                    :session_id,
                    :interaction_id,
                    :operation,
                    :payload_json,
                    :status,
                    :created_at
                )
                """
            ),
            {
                "proposal_id": proposal_id,
                "session_id": str(session_id),
                "interaction_id": interaction_id,
                "operation": operation,
                "payload_json": _json_dump(dict(payload)),
                "status": status,
                "created_at": _to_utc_iso(created_at),
            },
        )

    async def list_for_session(self, session_id: SessionId) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text(
                """
                SELECT
                    proposal_id,
                    session_id,
                    interaction_id,
                    operation,
                    payload_json,
                    status,
                    created_at
                FROM assistance_proposals
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                """
            ),
            {"session_id": str(session_id)},
        )
        rows = result.mappings().all()
        return [
            {
                "proposal_id": row["proposal_id"],
                "session_id": row["session_id"],
                "interaction_id": row["interaction_id"],
                "operation": row["operation"],
                "payload": _json_load_object(cast(str, row["payload_json"])),
                "status": row["status"],
                "created_at": _from_utc_iso(cast(str, row["created_at"])),
            }
            for row in rows
        ]


class SQLitePublicationAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: PublicationRecord) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO publication_attempts (
                    publication_id,
                    session_id,
                    session_revision,
                    adapter,
                    destination,
                    idempotency_key,
                    status,
                    requested_by,
                    external_reference,
                    error_json,
                    created_at,
                    completed_at
                )
                VALUES (
                    :publication_id,
                    :session_id,
                    :session_revision,
                    :adapter,
                    :destination,
                    :idempotency_key,
                    :status,
                    :requested_by,
                    :external_reference,
                    :error_json,
                    :created_at,
                    :completed_at
                )
                """
            ),
            {
                "publication_id": str(record.publication_id),
                "session_id": str(record.session_id),
                "session_revision": record.session_revision,
                "adapter": record.adapter,
                "destination": record.destination,
                "idempotency_key": record.idempotency_key,
                "status": record.status,
                "requested_by": record.requested_by,
                "external_reference": record.external_reference,
                "error_json": (None if record.error is None else record.error.model_dump_json()),
                "created_at": _to_utc_iso(record.created_at),
                "completed_at": (
                    None if record.completed_at is None else _to_utc_iso(record.completed_at)
                ),
            },
        )

    async def get_by_idempotency_key(
        self,
        session_id: SessionId,
        idempotency_key: str,
    ) -> PublicationRecord | None:
        result = await self._session.execute(
            text(
                """
                SELECT
                    publication_id,
                    session_id,
                    session_revision,
                    adapter,
                    destination,
                    idempotency_key,
                    status,
                    requested_by,
                    external_reference,
                    error_json,
                    created_at,
                    completed_at
                FROM publication_attempts
                WHERE session_id = :session_id
                  AND idempotency_key = :idempotency_key
                """
            ),
            {"session_id": str(session_id), "idempotency_key": idempotency_key},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return _publication_row_to_record(row)

    async def get(self, publication_id: PublicationId) -> PublicationRecord | None:
        result = await self._session.execute(
            text(f"SELECT {_PUBLICATION_COLUMNS} FROM publication_attempts WHERE publication_id = :publication_id"),
            {"publication_id": str(publication_id)},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return _publication_row_to_record(row)

    async def list_for_session(self, session_id: SessionId) -> list[PublicationRecord]:
        result = await self._session.execute(
            text(
                f"SELECT {_PUBLICATION_COLUMNS} FROM publication_attempts "
                "WHERE session_id = :session_id ORDER BY created_at ASC"
            ),
            {"session_id": str(session_id)},
        )
        return [_publication_row_to_record(row) for row in result.mappings().all()]

    async def complete(
        self,
        publication_id: PublicationId,
        *,
        status: PublicationStatus,
        completed_at: datetime,
        external_reference: str | None = None,
        error: ProblemDetail | None = None,
    ) -> PublicationRecord | None:
        result = await self._session.execute(
            text(
                """
                UPDATE publication_attempts
                SET status = :status,
                    external_reference = :external_reference,
                    error_json = :error_json,
                    completed_at = :completed_at
                WHERE publication_id = :publication_id
                """
            ),
            {
                "publication_id": str(publication_id),
                "status": status,
                "external_reference": external_reference,
                "error_json": None if error is None else error.model_dump_json(),
                "completed_at": _to_utc_iso(completed_at),
            },
        )
        if cast(CursorResult[Any], result).rowcount == 0:
            return None

        refreshed = await self._session.execute(
            text(
                """
                SELECT
                    publication_id,
                    session_id,
                    session_revision,
                    adapter,
                    destination,
                    idempotency_key,
                    status,
                    requested_by,
                    external_reference,
                    error_json,
                    created_at,
                    completed_at
                FROM publication_attempts
                WHERE publication_id = :publication_id
                """
            ),
            {"publication_id": str(publication_id)},
        )
        row = refreshed.mappings().first()
        if row is None:
            return None
        return _publication_row_to_record(row)


def _published_row_to_record(row: RowMapping) -> PublishedQuestionnaireRecord:
    return PublishedQuestionnaireRecord(
        questionnaire_id=QuestionnaireId(cast(str, row["questionnaire_id"])),
        version=cast(int, row["version"]),
        title=cast(str, row["title"]),
        output_contract=_json_load_object(cast(str, row["output_contract_json"])),
        output_needs=_json_load_list(cast(str, row["output_needs_json"])),
        questions=_json_load_list(cast(str, row["questions_json"])),
        health_policy=HealthPolicy.model_validate_json(cast(str, row["health_policy_json"])),
        assistance_policy=AssistancePolicy.model_validate_json(
            cast(str, row["assistance_policy_json"])
        ),
        content_hash=cast(str, row["content_hash"]),
        published_by=cast(str, row["published_by"]),
        published_at=_from_utc_iso(cast(str, row["published_at"])),
    )


def _session_row_to_record(row: RowMapping) -> SessionRecord:
    nav_json = cast(str | None, row.get("navigation_focus_json"))
    skip_raw = _json_load_object(cast(str, row.get("skip_dispositions_json") or "{}"))
    return SessionRecord(
        session_id=SessionId(cast(str, row["session_id"])),
        questionnaire_id=QuestionnaireId(cast(str, row["questionnaire_id"])),
        questionnaire_version=cast(int, row["questionnaire_version"]),
        revision=cast(int, row["revision"]),
        status=cast(SessionStatus, row["status"]),
        active_topic_id=cast(str | None, row["active_topic_id"]),
        answers=_json_load_object(cast(str, row["answers_json"])),
        generated_interactions=_json_load_list(cast(str, row["generated_interactions_json"])),
        skip_dispositions=_skip_dispositions_from_dict(skip_raw),
        navigation_focus=(
            None if nav_json is None else _navigation_focus_from_dict(json.loads(nav_json))
        ),
        created_by=cast(str, row["created_by"]),
        created_at=_from_utc_iso(cast(str, row["created_at"])),
        updated_at=_from_utc_iso(cast(str, row["updated_at"])),
    )


def _skip_dispositions_to_dict(dispositions: dict[str, SkipDisposition]) -> dict[str, Any]:
    return {
        qid: {
            "question_id": d.question_id,
            "accepted_revision": d.accepted_revision,
            "actor_id": d.actor_id,
            "skipped_at": _to_utc_iso(d.skipped_at),
        }
        for qid, d in dispositions.items()
    }


def _skip_dispositions_from_dict(raw: dict[str, Any]) -> dict[str, SkipDisposition]:
    result: dict[str, SkipDisposition] = {}
    for qid, d in raw.items():
        if isinstance(d, dict):
            result[qid] = SkipDisposition(
                question_id=d["question_id"],
                accepted_revision=d["accepted_revision"],
                actor_id=d["actor_id"],
                skipped_at=_from_utc_iso(d["skipped_at"]),
            )
    return result


def _navigation_focus_to_dict(focus: NavigationFocus) -> dict[str, Any]:
    return {
        "question_id": focus.question_id,
        "output_need_id": focus.output_need_id,
        "topic_id": focus.topic_id,
        "accepted_revision": focus.accepted_revision,
        "actor_id": focus.actor_id,
    }


def _navigation_focus_from_dict(raw: dict[str, Any]) -> NavigationFocus:
    return NavigationFocus(
        question_id=raw["question_id"],
        output_need_id=raw.get("output_need_id"),
        topic_id=raw.get("topic_id"),
        accepted_revision=raw["accepted_revision"],
        actor_id=raw["actor_id"],
    )


def _interaction_row_to_record(row: RowMapping) -> RuntimeInteractionRecord:
    snapshot_json = cast(str | None, row["interaction_snapshot_json"])
    submitted_value_json = cast(str, row["submitted_value_json"])
    return RuntimeInteractionRecord(
        interaction_id=InteractionId(cast(str, row["interaction_id"])),
        session_id=SessionId(cast(str, row["session_id"])),
        session_revision=cast(int, row["session_revision"]),
        kind=cast(InteractionKind, row["kind"]),
        interaction_snapshot=(None if snapshot_json is None else json.loads(snapshot_json)),
        submitted_value=json.loads(submitted_value_json),
        actor_id=cast(str, row["actor_id"]),
        metadata=_json_load_object(cast(str, row["metadata_json"])),
        created_at=_from_utc_iso(cast(str, row["created_at"])),
    )


def _publication_row_to_record(row: RowMapping) -> PublicationRecord:
    error_json = cast(str | None, row["error_json"])
    completed_at = cast(str | None, row["completed_at"])
    return PublicationRecord(
        publication_id=PublicationId(cast(str, row["publication_id"])),
        session_id=SessionId(cast(str, row["session_id"])),
        session_revision=cast(int, row["session_revision"]),
        adapter=cast(str, row["adapter"]),
        destination=cast(str, row["destination"]),
        idempotency_key=cast(str, row["idempotency_key"]),
        status=cast(PublicationStatus, row["status"]),
        requested_by=cast(str, row["requested_by"]),
        external_reference=cast(str | None, row["external_reference"]),
        error=(None if error_json is None else ProblemDetail.model_validate_json(error_json)),
        created_at=_from_utc_iso(cast(str, row["created_at"])),
        completed_at=(None if completed_at is None else _from_utc_iso(completed_at)),
    )


_PUBLICATION_COLUMNS = (
    "publication_id, session_id, session_revision, adapter, destination, "
    "idempotency_key, status, requested_by, external_reference, error_json, "
    "created_at, completed_at"
)


class SQLitePublishedArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def put_if_absent(self, record: PublishedArtifactRecord) -> bool:
        result = await self._session.execute(
            text(
                """
                INSERT INTO published_artifacts (
                    publication_id,
                    session_id,
                    session_revision,
                    adapter,
                    destination,
                    content_hash,
                    document_json,
                    created_at
                )
                VALUES (
                    :publication_id,
                    :session_id,
                    :session_revision,
                    :adapter,
                    :destination,
                    :content_hash,
                    :document_json,
                    :created_at
                )
                ON CONFLICT(publication_id) DO NOTHING
                """
            ),
            {
                "publication_id": str(record.publication_id),
                "session_id": str(record.session_id),
                "session_revision": record.session_revision,
                "adapter": record.adapter,
                "destination": record.destination,
                "content_hash": record.content_hash,
                "document_json": _json_dump(record.document),
                "created_at": _to_utc_iso(record.created_at),
            },
        )
        return cast(CursorResult[Any], result).rowcount > 0

    async def get(self, publication_id: PublicationId) -> PublishedArtifactRecord | None:
        result = await self._session.execute(
            text(
                """
                SELECT publication_id, session_id, session_revision, adapter,
                       destination, content_hash, document_json, created_at
                FROM published_artifacts
                WHERE publication_id = :publication_id
                """
            ),
            {"publication_id": str(publication_id)},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return PublishedArtifactRecord(
            publication_id=PublicationId(cast(str, row["publication_id"])),
            session_id=SessionId(cast(str, row["session_id"])),
            session_revision=cast(int, row["session_revision"]),
            adapter=cast(str, row["adapter"]),
            destination=cast(str, row["destination"]),
            content_hash=cast(str, row["content_hash"]),
            document=_json_load_object(cast(str, row["document_json"])),
            created_at=_from_utc_iso(cast(str, row["created_at"])),
        )

    async def count_for_session(self, session_id: SessionId) -> int:
        result = await self._session.execute(
            text("SELECT COUNT(*) AS n FROM published_artifacts WHERE session_id = :session_id"),
            {"session_id": str(session_id)},
        )
        row = result.mappings().first()
        return 0 if row is None else int(cast(int, row["n"]))
