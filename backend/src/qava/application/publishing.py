"""Publishing application service: preview and idempotent publication.

Reuses the deterministic session evaluation to build the result document, gates
on readiness, and drives an :class:`OutputAdapter` for the single publish side
effect. Republishing with the same idempotency key is a no-op, and an
indeterminate adapter outcome is recorded as ``outcome_unknown`` and resolved via
:meth:`reconcile`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from qava.domain.evaluation import SessionEvaluation, evaluate_session
from qava.domain.models import (
    ProblemDetail,
    PublicationId,
    PublicationRecord,
    PublishedQuestionnaireRecord,
    QuestionnaireId,
    SessionId,
    SessionRecord,
)
from qava.infrastructure.adapters.json_document import (
    JsonDocumentAdapter,
    content_hash,
    default_destination,
)
from qava.infrastructure.adapters.registry import RegistryAdapter
from qava.ports.output_adapter import IndeterminateOutcomeError, OutputAdapter
from qava.ports.repositories import (
    PublicationAttemptRepository,
    PublishedArtifactRepository,
    PublishedQuestionnaireRepository,
    SessionRepository,
)

_TERMINAL_STATUSES = frozenset({"succeeded", "failed", "denied"})


class SessionNotFoundError(KeyError):
    pass


class PublicationNotFoundError(KeyError):
    pass


class StaleRevisionError(Exception):
    pass


class NotReadyError(Exception):
    def __init__(self, message: str, problems: list[str] | None = None) -> None:
        super().__init__(message)
        self.problems = problems or []


class PublishingService:
    def __init__(
        self,
        *,
        questionnaire_repo: PublishedQuestionnaireRepository,
        session_repo: SessionRepository,
        attempts_repo: PublicationAttemptRepository,
        artifacts_repo: PublishedArtifactRepository,
        registry_adapter: OutputAdapter | None = None,
        adapter: OutputAdapter | None = None,
    ) -> None:
        self._questionnaires = questionnaire_repo
        self._sessions = session_repo
        self._attempts = attempts_repo
        self._artifacts = artifacts_repo
        json_adapter = adapter or JsonDocumentAdapter(artifacts_repo)
        resolved_registry_adapter = registry_adapter or RegistryAdapter(questionnaire_repo)
        self._adapters: dict[str, OutputAdapter] = {
            json_adapter.name: json_adapter,
            resolved_registry_adapter.name: resolved_registry_adapter,
        }

    async def preview(self, session_id: str) -> dict[str, object]:
        session, questionnaire, evaluation = await self._require_ready(session_id)
        document = dict(evaluation.projection.data)
        adapter = self._adapters["json_document"]
        destination = default_destination(str(session.session_id))
        validation = adapter.validate(document=document, destination=destination)
        if not validation.ok:
            raise NotReadyError("Result cannot be published.", validation.problems)
        preview = adapter.preview(document=document, destination=destination)
        return {
            "session_id": str(session.session_id),
            "revision": session.revision,
            "adapter": adapter.name,
            "destination": preview.destination,
            "content_hash": preview.content_hash,
            "document": preview.document,
        }

    async def publish(
        self,
        session_id: str,
        *,
        idempotency_key: str,
        expected_revision: int,
        requested_by: str,
        adapter_name: str = "json_document",
    ) -> PublicationRecord:
        session, _questionnaire, evaluation = await self._require_ready(session_id)
        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )

        existing = await self._attempts.get_by_idempotency_key(
            session.session_id, idempotency_key
        )
        if existing is not None:
            return existing

        adapter = self._adapters.get(adapter_name)
        if adapter is None:
            raise NotReadyError(f"Unknown output adapter {adapter_name!r}.")
        document = dict(evaluation.projection.data)
        destination = (
            "registry://questionnaires"
            if adapter.name == "registry"
            else default_destination(str(session.session_id))
        )
        validation = adapter.validate(document=document, destination=destination)
        if not validation.ok:
            raise NotReadyError("Result cannot be published.", validation.problems)

        now = datetime.now(UTC)
        publication_id = PublicationId(str(uuid.uuid4()))
        record = PublicationRecord(
            publication_id=publication_id,
            session_id=session.session_id,
            session_revision=session.revision,
            adapter=adapter.name,
            destination=destination,
            idempotency_key=idempotency_key,
            status="validating",
            requested_by=requested_by,
            created_at=now,
        )
        await self._attempts.create(record)

        try:
            receipt = await adapter.publish(
                publication_id=str(publication_id),
                session_id=str(session.session_id),
                session_revision=session.revision,
                document=document,
                destination=destination,
            )
        except IndeterminateOutcomeError as exc:
            completed = await self._attempts.complete(
                publication_id,
                status="outcome_unknown",
                completed_at=datetime.now(UTC),
                error=ProblemDetail(
                    type="https://qava.dev/problems/outcome-unknown",
                    title="Outcome Unknown",
                    detail=str(exc) or "The adapter could not confirm the publication outcome.",
                    status=202,
                ),
            )
            return completed or record

        completed = await self._attempts.complete(
            publication_id,
            status=receipt.status,
            completed_at=datetime.now(UTC),
            external_reference=receipt.external_reference,
        )
        return completed or record

    async def list_publications(self, session_id: str) -> list[PublicationRecord]:
        return await self._attempts.list_for_session(SessionId(session_id))

    async def reconcile(
        self,
        session_id: str,
        publication_id: str,
        *,
        requested_by: str,
    ) -> PublicationRecord:
        record = await self._attempts.get(PublicationId(publication_id))
        if record is None or str(record.session_id) != session_id:
            raise PublicationNotFoundError(publication_id)
        if record.status in _TERMINAL_STATUSES:
            return record

        adapter = self._adapters.get(record.adapter)
        if adapter is None:
            raise PublicationNotFoundError(publication_id)
        receipt = await adapter.reconcile(
            publication_id=publication_id,
            destination=record.destination,
        )
        error = (
            None
            if receipt.status == "succeeded"
            else ProblemDetail(
                type="https://qava.dev/problems/publication-failed",
                title="Publication Failed",
                detail=receipt.detail or "The publication could not be reconciled.",
                status=422,
            )
        )
        completed = await self._attempts.complete(
            PublicationId(publication_id),
            status=receipt.status,
            completed_at=datetime.now(UTC),
            external_reference=receipt.external_reference,
            error=error,
        )
        return completed or record

    async def _require_ready(
        self, session_id: str
    ) -> tuple[SessionRecord, PublishedQuestionnaireRecord, SessionEvaluation]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise SessionNotFoundError(session_id)
        questionnaire = await self._questionnaires.get(
            QuestionnaireId(str(session.questionnaire_id)), session.questionnaire_version
        )
        if questionnaire is None:
            raise SessionNotFoundError(session_id)
        evaluation = evaluate_session(questionnaire, session)
        if evaluation.health.readiness != "ready":
            raise NotReadyError(
                f"Session is not ready to publish (readiness: {evaluation.health.readiness})."
            )
        return session, questionnaire, evaluation


__all__ = [
    "NotReadyError",
    "PublicationNotFoundError",
    "PublishingService",
    "SessionNotFoundError",
    "StaleRevisionError",
    "content_hash",
]
