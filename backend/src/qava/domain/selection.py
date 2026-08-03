from __future__ import annotations

from typing import Any

from qava.domain.conditions import evaluate_condition


def select_next_interaction(
    *,
    questions: list[dict[str, Any]],
    answers: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the next interaction candidate or None when all applicable questions are answered.

    Priority:
      1. Required unanswered applicable questions, ascending by ``order``.
      2. Optional unanswered applicable questions, ascending by ``order``.

    An inapplicable question is never selected.
    """
    required_candidates: list[dict[str, Any]] = []
    optional_candidates: list[dict[str, Any]] = []

    for question in questions:
        question_id = question.get("id")
        if not isinstance(question_id, str):
            continue

        if not evaluate_condition(question.get("applicability"), answers):
            continue

        if question_id in answers:
            continue

        order = question.get("order", 0)
        is_required = bool(question.get("required", False))

        candidate = {"question_id": question_id, "order": order}
        if is_required:
            required_candidates.append(candidate)
        else:
            optional_candidates.append(candidate)

    if required_candidates:
        required_candidates.sort(key=lambda c: c["order"])
        return required_candidates[0]

    if optional_candidates:
        optional_candidates.sort(key=lambda c: c["order"])
        return optional_candidates[0]

    return None
