from __future__ import annotations

from typing import Literal

import pytest

from qava.application.assistance import AssistanceService
from qava.domain.models import AssistancePolicy, SessionId
from qava.infrastructure.assistance.fixture import FixtureAssistanceProvider
from qava.ports.assistance import AssistanceOperation


class _Proposals:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    async def create(self, proposal_id: str, **kwargs: object) -> None:
        self.records.append({"proposal_id": proposal_id, **kwargs})

    async def list_for_session(self, session_id: SessionId) -> list[dict[str, object]]:
        return self.records


def _policy(
    *operations: Literal["component", "ranking", "question", "clarification", "extraction"],
) -> AssistancePolicy:
    return AssistancePolicy(
        enabled_operations=list(operations),
        maximum_clarifications_per_interaction=1,
        maximum_generated_interactions_per_session=1,
        timeout_ms=1000,
        require_extraction_confirmation=True,
    )


@pytest.mark.asyncio
async def test_fixture_proposal_is_validated_and_audited() -> None:
    proposals = _Proposals()
    service = AssistanceService(FixtureAssistanceProvider(), proposals)

    result = await service.propose(
        session_id="session-1",
        operation="ranking",
        policy=_policy("ranking"),
        context={"eligible_interaction_ids": ["question-a", "question-b"]},
    )

    assert result.proposal is not None
    assert result.proposal.payload["interaction_ids"] == ["question-a", "question-b"]
    assert result.used_fallback is False
    assert proposals.records[0]["status"] == "accepted"
    payload = proposals.records[0]["payload"]
    assert isinstance(payload, dict)
    assert payload["model_identity"] == "fixture-assistance-v1"
    assert payload["policy_version"] == 1


@pytest.mark.asyncio
async def test_out_of_policy_or_invalid_fixture_uses_deterministic_fallback() -> None:
    proposals = _Proposals()
    provider = FixtureAssistanceProvider(
        fixtures={
            "ranking": {
                "interaction_ids": ["undeclared"],
                "confidence": 1.0,
                "reasons": ["bad"],
            }
        }
    )
    service = AssistanceService(provider, proposals)

    rejected = await service.propose(
        session_id="session-1",
        operation="ranking",
        policy=_policy(),
        context={"eligible_interaction_ids": ["question-a"]},
    )
    invalid = await service.propose(
        session_id="session-1",
        operation="ranking",
        policy=_policy("ranking"),
        context={"eligible_interaction_ids": ["question-a"]},
    )

    assert rejected.proposal is None and rejected.used_fallback
    assert invalid.proposal is None and invalid.used_fallback
    assert [record["status"] for record in proposals.records] == ["rejected", "rejected"]


@pytest.mark.asyncio
async def test_fixture_provider_covers_each_declared_operation() -> None:
    provider = FixtureAssistanceProvider()
    contexts: dict[AssistanceOperation, dict[str, object]] = {
        "component": {"allowed_components": ["short_text"]},
        "ranking": {"eligible_interaction_ids": ["question-a"]},
        "question": {},
        "clarification": {},
        "extraction": {"value": "normalized"},
    }

    for operation, context in contexts.items():
        proposal = await provider.propose(operation=operation, context=context)
        assert proposal is not None
        assert proposal.operation == operation
        assert proposal.model_identity == "fixture-assistance-v1"