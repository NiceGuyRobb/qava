"""API transport models — Pydantic schemas for FastAPI request/response shapes.

These are separate from domain records. Routers convert between them at the boundary.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class CreateDraftRequest(BaseModel):
    id: str
    title: str
    description: str | None = None
    output_contract: dict[str, Any]


class UpdateDraftRequest(BaseModel):
    operations: list[dict[str, Any]]


class AuthoringDecisionInput(BaseModel):
    decision_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    blocking: bool = True
    status: Literal["pending", "confirmed", "overridden", "rejected"] = "pending"
    resolution: dict[str, Any] | None = None


class ResolveDecisionRequest(BaseModel):
    decision_id: str = Field(min_length=1)
    action: Literal["confirm", "override", "reject"]
    resolution: dict[str, Any] | None = None


class RawDraftRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    output_contract: dict[str, Any]
    questions: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[AuthoringDecisionInput] = Field(default_factory=list)
    health_policy: dict[str, Any] | None = None
    assistance_policy: dict[str, Any] | None = None


class CreateSessionRequest(BaseModel):
    questionnaire_id: str
    questionnaire_version: int = Field(ge=1)


class SubmitAnswerRequest(BaseModel):
    interaction_id: str
    value: Any
    expected_revision: int = Field(ge=1)


class SkipInteractionRequest(BaseModel):
    interaction_id: str
    expected_revision: int = Field(ge=1)


class NavigateRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    output_need_id: str | None = None
    section_id: str | None = None


# ---------------------------------------------------------------------------
# Session View
# ---------------------------------------------------------------------------


class SessionSummary(BaseModel):
    id: str
    questionnaire_id: str
    questionnaire_version: int
    revision: int
    status: Literal["active", "completed"]


class Progress(BaseModel):
    satisfied_required: int
    total_required: int


class ComponentSpec(BaseModel):
    name: str
    version: int
    props: dict[str, Any]


class ChoiceOption(BaseModel):
    id: str
    label: str


class RuntimeInteraction(BaseModel):
    id: str
    kind: str
    output_need_ids: list[str]
    prompt: str
    reason: str
    required: bool
    answer_schema: dict[str, Any]
    component: ComponentSpec
    policy_limit: int | None = None
    choices: list[ChoiceOption] | None = None


class OutputNeedSummary(BaseModel):
    id: str
    target: str | None = None
    label: str | None = None
    required: bool
    criticality: str
    question_id: str
    topic_id: str | None = None


class ResultProjection(BaseModel):
    session_id: str
    revision: int
    status: str
    data: dict[str, Any]
    provenance: dict[str, list[str]]
    unresolved_output_needs: list[OutputNeedSummary]
    issues: list[Any] = Field(default_factory=list)


class AttentionItemResponse(BaseModel):
    code: str
    severity: str
    message: str
    recommended_action: str
    output_need_id: str | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class HealthAssessment(BaseModel):
    revision: int
    score: int
    readiness: str
    dimensions: dict[str, int]
    attention: list[AttentionItemResponse]
    calculation_version: int


class SessionView(BaseModel):
    session: SessionSummary
    progress: Progress
    current_interaction: RuntimeInteraction | None
    result: ResultProjection
    health: HealthAssessment
    actions: list[str]
    changed_paths: list[str]


# ---------------------------------------------------------------------------
# Publication (US2)
# ---------------------------------------------------------------------------


class ResultPreview(BaseModel):
    session_id: str
    revision: int
    adapter: str
    destination: str
    content_hash: str
    document: dict[str, Any]


class PublishRequest(BaseModel):
    idempotency_key: str = Field(min_length=1)
    expected_revision: int = Field(ge=1)
    adapter: Literal["json_document", "registry"] = "json_document"


class PublicationReceipt(BaseModel):
    publication_id: str
    session_id: str
    session_revision: int
    adapter: str
    destination: str
    idempotency_key: str
    status: str
    requested_by: str
    external_reference: str | None = None
    error: dict[str, Any] | None = None


class PublicationList(BaseModel):
    publications: list[PublicationReceipt]
