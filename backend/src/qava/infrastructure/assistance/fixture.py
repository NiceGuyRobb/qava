from __future__ import annotations

from typing import Any, TypeGuard, cast

from qava.ports.assistance import AssistanceOperation, AssistanceProposal


class FixtureAssistanceProvider:
    """Hardcoded proposals used to prove the validated assistance boundary."""

    def __init__(self, fixtures: dict[str, dict[str, Any]] | None = None) -> None:
        self._fixtures = fixtures or {}

    async def propose(
        self, *, operation: AssistanceOperation, context: dict[str, Any]
    ) -> AssistanceProposal | None:
        payload = self._fixtures.get(operation)
        if payload is None:
            payload = _default_payload(operation, context)
        if payload is None:
            return None
        confidence = payload.get("confidence", 0.8)
        reasons = payload.get("reasons", ["Fixture proposal."])
        if not isinstance(confidence, int | float) or not _is_string_list(reasons):
            return None
        return AssistanceProposal(
            operation=operation,
            payload={
                key: value
                for key, value in payload.items()
                if key not in {"confidence", "reasons"}
            },
            confidence=float(confidence),
            reasons=reasons,
            model_identity="fixture-assistance-v1",
            policy_version=1,
            evidence=[{"source": "fixture"}],
        )


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(
        isinstance(item, str) for item in cast(list[object], value)
    )


def _default_payload(
    operation: AssistanceOperation, context: dict[str, Any]
) -> dict[str, Any] | None:
    if operation == "ranking":
        eligible = context.get("eligible_interaction_ids")
        if _is_string_list(eligible):
            return {
                "interaction_ids": eligible,
                "confidence": 0.8,
                "reasons": ["Fixture preserves deterministic eligible order."],
            }
    if operation == "component":
        components = context.get("allowed_components")
        if _is_string_list(components) and components:
            return {
                "component": components[0],
                "confidence": 0.8,
                "reasons": ["Fixture selects the first allowed component."],
            }
    if operation == "question":
        return {
            "prompt": "Fixture question proposal.",
            "confidence": 0.8,
            "reasons": ["Fixture provides deterministic question wording."],
        }
    if operation == "clarification":
        return {
            "prompt": "Fixture clarification proposal.",
            "confidence": 0.8,
            "reasons": ["Fixture provides deterministic clarification wording."],
        }
    if operation == "extraction" and "value" in context:
        return {
            "value": context["value"],
            "confidence": 0.8,
            "reasons": ["Fixture returns the supplied bounded value."],
        }
    return None