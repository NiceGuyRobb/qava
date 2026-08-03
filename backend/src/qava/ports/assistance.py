from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

AssistanceOperation = Literal["component", "ranking", "question", "clarification", "extraction"]


class AssistanceProposal(BaseModel):
    operation: AssistanceOperation
    payload: dict[str, Any]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1)
    model_identity: str
    policy_version: int = Field(ge=1)
    evidence: list[dict[str, Any]] = Field(
        default_factory=lambda: list[dict[str, Any]]()
    )


class AssistanceProvider(Protocol):
    async def propose(
        self, *, operation: AssistanceOperation, context: dict[str, Any]
    ) -> AssistanceProposal | None: ...