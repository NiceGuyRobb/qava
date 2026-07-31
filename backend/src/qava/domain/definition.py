from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DefinitionIssue:
    code: str
    message: str
    pointer: str


def derive_output_needs(output_contract: dict[str, Any]) -> list[dict[str, Any]]:
    root_type = output_contract.get("type")
    if root_type != "object":
        return []

    properties = output_contract.get("properties", {})
    required = {entry for entry in output_contract.get("required", []) if isinstance(entry, str)}

    needs: list[dict[str, Any]] = []
    for key in sorted(properties.keys()):
        schema = properties.get(key)
        if not isinstance(schema, dict):
            continue

        pointer = f"/{key}"
        is_required = key in required
        needs.append(
            {
                "id": f"need:{key}",
                "target": pointer,
                "value_schema": schema,
                "required": is_required,
                "criticality": "blocking" if is_required else "normal",
                "weight": 1.0,
            }
        )

    return needs


def validate_publication(
    *,
    output_contract: dict[str, Any],
    questions: list[dict[str, Any]],
) -> list[DefinitionIssue]:
    issues: list[DefinitionIssue] = []
    output_needs = derive_output_needs(output_contract)

    declared_targets = _declared_mapping_targets(questions)

    for need in output_needs:
        target = need["target"]
        is_served = any(
            declared == target or declared.startswith(f"{target}/") for declared in declared_targets
        )
        if need["required"] and not is_served:
            issues.append(
                DefinitionIssue(
                    code="missing_required_target",
                    message=f"No question mapping target serves required output need at {target}.",
                    pointer=target,
                )
            )

    seen_question_ids: set[str] = set()
    for question in questions:
        question_id = question.get("id")
        if not isinstance(question_id, str):
            continue
        if question_id in seen_question_ids:
            issues.append(
                DefinitionIssue(
                    code="duplicate_question_id",
                    message=f"Question id {question_id!r} must be unique.",
                    pointer=f"/questions/{question_id}",
                )
            )
        seen_question_ids.add(question_id)

    return issues


def compile_draft(
    *,
    draft_id: str,
    title: str,
    output_contract: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    output_needs = derive_output_needs(output_contract)
    issues = validate_publication(output_contract=output_contract, questions=questions)

    return {
        "id": draft_id,
        "title": title,
        "output_contract": output_contract,
        "output_needs": output_needs,
        "questions": questions,
        "validation_issues": [
            {"code": issue.code, "message": issue.message, "pointer": issue.pointer}
            for issue in issues
        ],
        "compiled_at": datetime.now(UTC).isoformat(),
    }


def _declared_mapping_targets(questions: list[dict[str, Any]]) -> set[str]:
    targets: set[str] = set()
    for question in questions:
        mapping = question.get("mapping")
        if not isinstance(mapping, dict):
            continue
        target = mapping.get("target")
        if isinstance(target, str):
            targets.add(target)
    return targets
