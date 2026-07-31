from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal, Protocol

from qava.domain.models import (
    InteractionId,
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
)

JsonObject = dict[str, Any]
ProposalStatus = Literal["pending", "accepted", "rejected", "failed"]
ProposalOperation = Literal["component", "ranking", "question", "clarification", "extraction"]


class DraftRepository(Protocol):
    async def upsert(
        self,
        draft_id: str,
        payload: Mapping[str, Any],
        *,
        updated_at: datetime,
    ) -> None: ...

    async def get(self, draft_id: str) -> JsonObject | None: ...

    async def delete(self, draft_id: str) -> bool: ...


class PublishedQuestionnaireRepository(Protocol):
    async def insert(self, record: PublishedQuestionnaireRecord) -> None: ...

    async def get(
        self,
        questionnaire_id: QuestionnaireId,
        version: int,
    ) -> PublishedQuestionnaireRecord | None: ...

    async def get_latest_version(self, questionnaire_id: QuestionnaireId) -> int | None: ...


class SessionRepository(Protocol):
    async def create(self, record: SessionRecord) -> None: ...

    async def get(self, session_id: SessionId) -> SessionRecord | None: ...

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
    ) -> SessionRecord | None: ...

    async def delete(self, session_id: SessionId) -> bool: ...


class InteractionRepository(Protocol):
    async def append(self, record: RuntimeInteractionRecord) -> None: ...

    async def list_for_session(self, session_id: SessionId) -> list[RuntimeInteractionRecord]: ...


class AssistanceProposalRepository(Protocol):
    async def create(
        self,
        proposal_id: str,
        *,
        session_id: SessionId,
        operation: ProposalOperation,
        payload: Mapping[str, Any],
        status: ProposalStatus,
        created_at: datetime,
        interaction_id: InteractionId | None = None,
    ) -> None: ...

    async def list_for_session(self, session_id: SessionId) -> list[JsonObject]: ...


class PublicationAttemptRepository(Protocol):
    async def create(self, record: PublicationRecord) -> None: ...

    async def get(self, publication_id: PublicationId) -> PublicationRecord | None: ...

    async def get_by_idempotency_key(
        self,
        session_id: SessionId,
        idempotency_key: str,
    ) -> PublicationRecord | None: ...

    async def list_for_session(self, session_id: SessionId) -> list[PublicationRecord]: ...

    async def complete(
        self,
        publication_id: PublicationId,
        *,
        status: PublicationStatus,
        completed_at: datetime,
        external_reference: str | None = None,
        error: ProblemDetail | None = None,
    ) -> PublicationRecord | None: ...


class PublishedArtifactRepository(Protocol):
    async def put_if_absent(self, record: PublishedArtifactRecord) -> bool: ...

    async def get(self, publication_id: PublicationId) -> PublishedArtifactRecord | None: ...

    async def count_for_session(self, session_id: SessionId) -> int: ...
