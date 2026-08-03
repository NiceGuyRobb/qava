from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeGuard, cast

from qava.domain.models import AssistancePolicy, InteractionId, SessionId
from qava.ports.assistance import AssistanceOperation, AssistanceProposal, AssistanceProvider
from qava.ports.repositories import AssistanceProposalRepository, ProposalStatus


@dataclass(frozen=True)
class AssistanceResult:
    proposal: AssistanceProposal | None
    used_fallback: bool


class AssistanceService:
    def __init__(
        self,
        provider: AssistanceProvider | None,
        proposals: AssistanceProposalRepository,
    ) -> None:
        self._provider = provider
        self._proposals = proposals

    async def propose(
        self,
        *,
        session_id: str,
        operation: AssistanceOperation,
        policy: AssistancePolicy,
        context: dict[str, Any],
        interaction_id: str | None = None,
    ) -> AssistanceResult:
        if operation not in policy.enabled_operations or self._provider is None:
            await self._record(
                session_id,
                operation,
                {"reason": "disabled_or_not_permitted"},
                "rejected",
                interaction_id,
            )
            return AssistanceResult(proposal=None, used_fallback=True)
        proposal = await self._provider.propose(operation=operation, context=context)
        if proposal is None or not _is_valid(proposal, context):
            await self._record(
                session_id,
                operation,
                {"reason": "missing_or_invalid"},
                "rejected",
                interaction_id,
            )
            return AssistanceResult(proposal=None, used_fallback=True)
        payload = proposal.model_dump()
        if operation == "extraction" and policy.require_extraction_confirmation:
            payload["requires_confirmation"] = True
        await self._record(session_id, operation, payload, "accepted", interaction_id)
        return AssistanceResult(proposal=proposal, used_fallback=False)

    async def _record(
        self,
        session_id: str,
        operation: AssistanceOperation,
        payload: dict[str, Any],
        status: ProposalStatus,
        interaction_id: str | None,
    ) -> None:
        await self._proposals.create(
            str(uuid.uuid4()),
            session_id=SessionId(session_id),
            operation=operation,
            payload=payload,
            status=status,
            created_at=datetime.now(UTC),
            interaction_id=None if interaction_id is None else InteractionId(interaction_id),
        )


def _is_valid(proposal: AssistanceProposal, context: dict[str, Any]) -> bool:
    if proposal.operation == "ranking":
        ranked = proposal.payload.get("interaction_ids")
        eligible = context.get("eligible_interaction_ids")
        return _is_string_list(ranked) and _is_string_list(eligible) and all(
            item in eligible for item in ranked
        )
    if proposal.operation == "component":
        return proposal.payload.get("component") in context.get("allowed_components", [])
    return True


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(
        isinstance(item, str) for item in cast(list[object], value)
    )