"""Authoring application service: draft create, update, validate, publish."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from qava.domain.definition import compile_draft, validate_publication
from qava.domain.models import (
    AssistancePolicy,
    AuthoringDecision,
    HealthPolicy,
    PublishedQuestionnaireRecord,
    QuestionnaireId,
)
from qava.infrastructure.database.repositories import (
    SQLiteDraftRepository,
    SQLitePublishedQuestionnaireRepository,
)


class AuthoringService:
    def __init__(
        self,
        draft_repo: SQLiteDraftRepository,
        questionnaire_repo: SQLitePublishedQuestionnaireRepository,
    ) -> None:
        self._drafts = draft_repo
        self._questionnaires = questionnaire_repo

    async def create_draft(
        self,
        *,
        draft_id: str,
        title: str,
        output_contract: dict[str, Any],
        description: str | None = None,
        questions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        compiled = compile_draft(
            draft_id=draft_id,
            title=title,
            output_contract=output_contract,
            questions=questions or [],
        )
        compiled["description"] = description
        compiled["decisions"] = []
        compiled["pending_decisions"] = []
        compiled["health_policy"] = _default_health_policy().model_dump()
        compiled["assistance_policy"] = _default_assistance_policy().model_dump()
        now = datetime.now(UTC)
        await self._drafts.upsert(draft_id, compiled, updated_at=now)
        saved = await self.get_draft(draft_id)
        assert saved is not None
        return saved

    async def get_draft(self, draft_id: str) -> dict[str, Any] | None:
        draft = await self._drafts.get(draft_id)
        if draft is None:
            return None
        _surface_pending_decisions(draft)
        return draft

    async def delete_draft(self, draft_id: str) -> bool:
        return await self._drafts.delete(draft_id)

    async def update_draft(
        self,
        draft_id: str,
        *,
        operations: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        current = await self._drafts.get(draft_id)
        if current is None:
            return None

        for op in operations:
            op_type = op.get("operation")
            if op_type == "upsert_question":
                question = op.get("question")
                if isinstance(question, dict) and isinstance(question.get("id"), str):
                    questions: list[dict[str, Any]] = list(current.get("questions", []))
                    existing_idx = next(
                        (i for i, q in enumerate(questions) if q.get("id") == question["id"]),
                        None,
                    )
                    if existing_idx is not None:
                        questions[existing_idx] = question
                    else:
                        questions.append(question)
                    current["questions"] = questions

        _recompile_draft(current)

        now = datetime.now(UTC)
        await self._drafts.upsert(draft_id, current, updated_at=now)
        return await self.get_draft(draft_id)

    async def resolve_decision(
        self,
        draft_id: str,
        *,
        decision_id: str,
        action: str,
        resolution: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        current = await self._drafts.get(draft_id)
        if current is None:
            return None

        decisions = _validated_decisions(current.get("decisions", []))
        index = next(
            (position for position, decision in enumerate(decisions) if decision.decision_id == decision_id),
            None,
        )
        if index is None:
            raise ValueError(f"Authoring decision {decision_id!r} not found.")

        decision = decisions[index]
        if decision.status != "pending":
            raise ValueError(f"Authoring decision {decision_id!r} is already resolved.")
        if action == "override" and resolution is None:
            raise ValueError("An override requires a resolution object.")

        if action == "confirm":
            status = "confirmed"
            chosen = resolution or _candidate_resolution(decision)
        elif action == "override":
            status = "overridden"
            chosen = resolution
        elif action == "reject":
            status = "rejected"
            chosen = None
        else:
            raise ValueError(f"Unsupported authoring decision action {action!r}.")

        decisions[index] = decision.model_copy(update={"status": status, "resolution": chosen})
        current["decisions"] = [decision.model_dump(exclude_none=True) for decision in decisions]
        _recompile_draft(current)
        await self._drafts.upsert(draft_id, current, updated_at=datetime.now(UTC))
        return await self.get_draft(draft_id)

    async def replace_raw_draft(
        self,
        draft_id: str,
        *,
        title: str,
        description: str | None,
        output_contract: dict[str, Any],
        questions: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        health_policy: dict[str, Any] | None,
        assistance_policy: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        current = await self._drafts.get(draft_id)
        if current is None:
            return None

        current["title"] = title
        current["description"] = description
        current["output_contract"] = output_contract
        current["questions"] = questions
        current["decisions"] = [
            decision.model_dump(exclude_none=True)
            for decision in _validated_decisions(decisions)
        ]
        if health_policy is not None:
            current["health_policy"] = HealthPolicy.model_validate(health_policy).model_dump()
        if assistance_policy is not None:
            current["assistance_policy"] = AssistancePolicy.model_validate(assistance_policy).model_dump()
        _recompile_draft(current)
        await self._drafts.upsert(draft_id, current, updated_at=datetime.now(UTC))
        return await self.get_draft(draft_id)

    async def publish_draft(
        self,
        draft_id: str,
        *,
        published_by: str,
    ) -> PublishedQuestionnaireRecord | None:
        draft = await self._drafts.get(draft_id)
        if draft is None:
            return None

        pending_blocking = [
            decision
            for decision in _validated_decisions(draft.get("decisions", []))
            if decision.blocking and decision.status == "pending"
        ]
        if pending_blocking:
            raise ValueError(
                "Cannot publish while a pending blocking decision remains: "
                f"{pending_blocking[0].decision_id!r}."
            )

        output_contract = draft.get("output_contract", {})
        questions = draft.get("questions", [])

        issues = validate_publication(output_contract=output_contract, questions=questions)
        blocking = [iss for iss in issues if True]  # all issues block for now
        if blocking:
            raise ValueError(f"Cannot publish draft {draft_id!r}: {blocking[0].message}")

        latest_version = await self._questionnaires.get_latest_version(QuestionnaireId(draft_id))
        new_version = (latest_version or 0) + 1

        raw = json.dumps(
            {"id": draft_id, "version": new_version, "contract": output_contract},
            sort_keys=True,
        )
        content_hash = hashlib.sha256(raw.encode()).hexdigest()

        health_policy_raw = draft.get("health_policy", {})
        assistance_policy_raw = draft.get("assistance_policy", {})

        record = PublishedQuestionnaireRecord(
            questionnaire_id=QuestionnaireId(draft_id),
            version=new_version,
            title=draft["title"],
            output_contract=output_contract,
            output_needs=draft.get("output_needs", []),
            questions=questions,
            health_policy=HealthPolicy.model_validate(health_policy_raw),
            assistance_policy=AssistancePolicy.model_validate(assistance_policy_raw),
            content_hash=content_hash,
            published_by=published_by,
            published_at=datetime.now(UTC),
        )

        await self._questionnaires.insert(record)
        return record


def _recompile_draft(draft: dict[str, Any]) -> None:
    """Refresh derived draft fields after either guided or raw authoring changes."""
    recompiled = compile_draft(
        draft_id=draft["id"],
        title=draft["title"],
        output_contract=draft.get("output_contract", {}),
        questions=draft.get("questions", []),
    )
    draft["output_needs"] = recompiled["output_needs"]
    draft["validation_issues"] = recompiled["validation_issues"]
    decisions = _validated_decisions(draft.get("decisions", []))
    draft["decisions"] = [decision.model_dump(exclude_none=True) for decision in decisions]
    draft["pending_decisions"] = [
        decision.model_dump(exclude_none=True)
        for decision in decisions
        if decision.status == "pending"
    ]


def _validated_decisions(raw_decisions: object) -> list[AuthoringDecision]:
    if not isinstance(raw_decisions, list):
        raise ValueError("Draft decisions must be a list.")
    return [AuthoringDecision.model_validate(decision) for decision in raw_decisions]


def _surface_pending_decisions(draft: dict[str, Any]) -> None:
    draft["pending_decisions"] = [
        decision.model_dump(exclude_none=True)
        for decision in _validated_decisions(draft.get("decisions", []))
        if decision.status == "pending"
    ]


def _candidate_resolution(decision: AuthoringDecision) -> dict[str, Any] | None:
    if not decision.candidates:
        return None
    return dict(decision.candidates[0])


def _default_health_policy() -> HealthPolicy:
    return HealthPolicy(
        calculation_version=1,
        completeness_weight=1.0,
        validity_weight=1.0,
        confidence_weight=1.0,
        consistency_weight=1.0,
        specificity_weight=1.0,
        minimum_validity=0,
        block_on="blocking",
    )


def _default_assistance_policy() -> AssistancePolicy:
    return AssistancePolicy(
        enabled_operations=[],
        maximum_clarifications_per_interaction=0,
        maximum_generated_interactions_per_session=0,
        timeout_ms=5000,
        require_extraction_confirmation=True,
    )
