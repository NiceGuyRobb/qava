from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def evaluate_condition(condition: Mapping[str, Any] | None, answers: Mapping[str, Any]) -> bool:
    if condition is None:
        return True

    alternatives = condition.get("any")
    if isinstance(alternatives, list):
        return any(
            evaluate_condition(alternative, answers)
            for alternative in alternatives
            if isinstance(alternative, Mapping)
        )

    source_question_id = condition.get("source_question_id")
    operator = condition.get("operator")

    if not isinstance(source_question_id, str) or not isinstance(operator, str):
        return False
    if source_question_id not in answers:
        return False

    source_value = answers[source_question_id]
    source_value_path = condition.get("source_value_path")
    if isinstance(source_value_path, str):
        for part in source_value_path.split("."):
            if not isinstance(source_value, Mapping) or part not in source_value:
                return False
            source_value = source_value[part]

    if operator == "equals":
        return source_value == condition.get("value")

    if operator == "contains":
        expected = condition.get("value")
        if isinstance(source_value, list):
            return expected in source_value
        if isinstance(source_value, str) and isinstance(expected, str):
            return expected in source_value
        return False

    if operator == "exists":
        return source_value is not None

    return False
