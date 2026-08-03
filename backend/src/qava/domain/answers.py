from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from jsonschema import Draft202012Validator


def validate_answer(question: Mapping[str, Any], answer_value: Any) -> list[str]:
    issues: list[str] = []

    answer_schema = question.get("answer_schema")
    if not isinstance(answer_schema, dict):
        return ["answer_schema missing or invalid"]

    validator = Draft202012Validator(answer_schema)
    validation_errors = sorted(
        validator.iter_errors(answer_value),
        key=lambda error: str(error.path),
    )
    issues.extend(error.message for error in validation_errors)

    if not validation_errors:
        issues.extend(_validate_unique_selection_item_ids(answer_value))

    choices = question.get("choices")
    if isinstance(choices, list) and choices:
        issues.extend(_validate_choice_ids(choices, answer_value))

    return issues


def _validate_unique_selection_item_ids(answer_value: Any) -> list[str]:
    if not isinstance(answer_value, Mapping):
        return []
    selections = answer_value.get("selections")
    if not isinstance(selections, list):
        return []

    item_ids = [
        selection.get("item_id")
        for selection in selections
        if isinstance(selection, Mapping) and isinstance(selection.get("item_id"), str)
    ]
    seen: set[str] = set()
    duplicates: list[str] = []
    for item_id in item_ids:
        if item_id in seen:
            duplicates.append(item_id)
        else:
            seen.add(item_id)
    if not duplicates:
        return []
    return [f"selections contains duplicate item_id values: {duplicates!r}"]


def _validate_choice_ids(choices: Sequence[object], answer_value: Any) -> list[str]:
    choice_ids = [
        choice.get("id")
        for choice in choices
        if isinstance(choice, dict) and isinstance(choice.get("id"), str)
    ]
    allowed = set(choice_ids)

    issues: list[str] = []
    if isinstance(answer_value, list):
        invalid = [value for value in answer_value if value not in allowed]
        if invalid:
            issues.append(f"choice_id list contains unknown values: {invalid!r}")
        return issues

    if answer_value not in allowed:
        issues.append(f"choice_id {answer_value!r} is not declared")

    return issues
