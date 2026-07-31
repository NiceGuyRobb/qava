from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, NewType

from pydantic import BaseModel, Field

QuestionnaireId = NewType("QuestionnaireId", str)
SessionId = NewType("SessionId", str)
InteractionId = NewType("InteractionId", str)
PublicationId = NewType("PublicationId", str)

RoleName = Literal["author", "respondent", "publisher"]
SessionStatus = Literal["active", "completed"]
Readiness = Literal["not_ready", "needs_attention", "ready"]
PublicationStatus = Literal["validating", "succeeded", "failed", "outcome_unknown", "denied"]


class ProblemDetail(BaseModel):
    type: str
    title: str
    detail: str
    status: int
    instance: str | None = None


class HealthPolicy(BaseModel):
    calculation_version: int = Field(ge=1)
    completeness_weight: float = Field(gt=0)
    validity_weight: float = Field(gt=0)
    confidence_weight: float = Field(gt=0)
    consistency_weight: float = Field(gt=0)
    specificity_weight: float = Field(gt=0)
    minimum_validity: int = Field(ge=0, le=100)
    block_on: Literal["blocking", "warning"]


class AssistancePolicy(BaseModel):
    enabled_operations: list[
        Literal["component", "ranking", "question", "clarification", "extraction"]
    ]
    maximum_clarifications_per_interaction: int = Field(ge=0, le=2)
    maximum_generated_interactions_per_session: int = Field(ge=0, le=1000)
    timeout_ms: int = Field(gt=0)
    require_extraction_confirmation: bool = True


class AuthoringDecision(BaseModel):
    decision_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    blocking: bool = True
    status: Literal["pending", "confirmed", "overridden", "rejected"] = "pending"
    resolution: dict[str, Any] | None = None


@dataclass(frozen=True)
class SkipDisposition:
    question_id: str
    accepted_revision: int
    actor_id: str
    skipped_at: datetime


@dataclass(frozen=True)
class NavigationFocus:
    question_id: str
    output_need_id: str | None
    topic_id: str | None
    accepted_revision: int
    actor_id: str


class PublishedQuestionnaireRecord(BaseModel):
    questionnaire_id: QuestionnaireId
    version: int = Field(ge=1)
    title: str
    output_contract: dict[str, Any]
    output_needs: list[dict[str, Any]]
    questions: list[dict[str, Any]]
    health_policy: HealthPolicy
    assistance_policy: AssistancePolicy
    content_hash: str
    published_by: str
    published_at: datetime


class SessionRecord(BaseModel):
    session_id: SessionId
    questionnaire_id: QuestionnaireId
    questionnaire_version: int = Field(ge=1)
    revision: int = Field(ge=1)
    status: SessionStatus
    active_topic_id: str | None = None
    answers: dict[str, Any] = Field(default_factory=dict)
    generated_interactions: list[dict[str, Any]] = Field(default_factory=list)
    skip_dispositions: dict[str, SkipDisposition] = Field(default_factory=dict)
    navigation_focus: NavigationFocus | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class RuntimeInteractionRecord(BaseModel):
    interaction_id: InteractionId
    session_id: SessionId
    session_revision: int = Field(ge=1)
    kind: Literal[
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
    interaction_snapshot: dict[str, Any] | None = None
    submitted_value: Any = None
    actor_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AttentionItem(BaseModel):
    code: str
    severity: Literal["info", "warning", "blocking"]
    message: str
    recommended_action: str
    output_need_id: str | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class HealthAssessmentRecord(BaseModel):
    revision: int = Field(ge=1)
    score: int = Field(ge=0, le=100)
    readiness: Readiness
    dimensions: dict[str, int]
    attention: list[AttentionItem] = Field(default_factory=list)
    calculation_version: int = Field(ge=1)


class PublicationRecord(BaseModel):
    publication_id: PublicationId
    session_id: SessionId
    session_revision: int = Field(ge=1)
    adapter: str
    destination: str
    idempotency_key: str
    status: PublicationStatus
    requested_by: str
    external_reference: str | None = None
    error: ProblemDetail | None = None
    created_at: datetime
    completed_at: datetime | None = None


class PublishedArtifactRecord(BaseModel):
    publication_id: PublicationId
    session_id: SessionId
    session_revision: int = Field(ge=1)
    adapter: str
    destination: str
    content_hash: str
    document: dict[str, Any]
    created_at: datetime
