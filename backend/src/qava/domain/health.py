from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from qava.domain.answers import validate_answer
from qava.domain.models import AttentionItem, HealthAssessmentRecord, HealthPolicy, Readiness

# A validator callable passed in for T030 adapter dry-run: takes the projected
# data dict and returns a list of problem strings (empty = valid).
AdapterValidator = Callable[[dict[str, Any]], list[str]]


def assess_health(
    *,
    output_needs: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    answers: dict[str, Any],
    policy: HealthPolicy,
    revision: int,
    adapter_validator: AdapterValidator | None = None,
) -> HealthAssessmentRecord:
    attention: list[AttentionItem] = []

    # --- Completeness: fraction of required output needs with any answer ---
    question_by_id = {q["id"]: q for q in questions if isinstance(q.get("id"), str)}
    need_answered = _needs_answered(output_needs, questions, answers)
    required_needs = [n for n in output_needs if n.get("required")]
    if required_needs:
        answered_required = sum(
            1 for n in required_needs if need_answered.get(str(n["id"])) if "id" in n
        )
        completeness = int(100 * answered_required / len(required_needs))
    else:
        completeness = 100

    # --- Validity: fraction of answered questions passing schema validation ---
    total_answered = sum(1 for qid in answers if qid in question_by_id)
    valid_count = 0
    for qid, answer_value in answers.items():
        question = question_by_id.get(qid)
        if question is None:
            continue
        issues = validate_answer(question, answer_value)
        if not issues:
            valid_count += 1
        else:
            output_need_ids: list[str] = [
                nid for nid in question.get("output_need_ids", []) if isinstance(nid, str)
            ]
            attention.append(
                AttentionItem(
                    code="invalid_answer",
                    severity="blocking",
                    message=f"Answer for {qid!r} failed validation: {issues[0]}",
                    recommended_action=f"Correct your answer for {qid!r}.",
                    output_need_id=output_need_ids[0] if output_need_ids else None,
                    evidence=[{"question_id": qid, "issues": issues}],
                )
            )

    if total_answered > 0:
        validity = int(100 * valid_count / total_answered)
    else:
        validity = 100

    # --- Unanswered required needs produce blocking attention ---
    for need in required_needs:
        need_id = need.get("id")
        if need_id and not need_answered.get(need_id):
            attention.append(
                AttentionItem(
                    code="unanswered_required_need",
                    severity="blocking",
                    message=f"Required output need {need_id!r} has no accepted answer.",
                    recommended_action="Answer the associated question.",
                    output_need_id=need_id,
                )
            )

    # --- Confidence: fraction answered; attention for thinly-evidenced required needs ---
    confidence, confidence_attention = _rule_confidence(answers, questions, output_needs)
    attention.extend(confidence_attention)

    # --- Consistency: detect contradictions among questions sharing an output need ---
    consistency, consistency_attention = _rule_consistency(answers, questions, output_needs)
    attention.extend(consistency_attention)

    # --- Specificity: flag imprecise (empty-string) answers ---
    specificity, specificity_attention = _rule_specificity(answers, questions)
    attention.extend(specificity_attention)

    # --- Adapter dry-run validity (T030, optional) ---
    if adapter_validator is not None:
        # Build a minimal projected data dict from direct-mapped answers for dry-run.
        projected: dict[str, Any] = {}
        for q in questions:
            qid = q.get("id")
            if not isinstance(qid, str) or qid not in answers:
                continue
            mapping = q.get("mapping", {})
            if isinstance(mapping, dict) and mapping.get("mode") == "direct":
                target = mapping.get("target", "")
                if isinstance(target, str) and target.startswith("/"):
                    projected[target.lstrip("/")] = answers[qid]
        problems = adapter_validator(projected)
        if problems:
            for problem in problems:
                attention.append(
                    AttentionItem(
                        code="adapter_validation_failed",
                        severity="blocking",
                        message=f"Adapter validation: {problem}",
                        recommended_action="Address the validation issue before publishing.",
                        output_need_id=None,
                    )
                )
            # Reduce validity proportionally to the number of adapter problems.
            adapter_penalty = min(100, len(problems) * 20)
            validity = max(0, validity - adapter_penalty)

    # --- Weighted headline score ---
    weights = [
        (completeness, policy.completeness_weight),
        (validity, policy.validity_weight),
        (confidence, policy.confidence_weight),
        (consistency, policy.consistency_weight),
        (specificity, policy.specificity_weight),
    ]
    total_weight = sum(w for _, w in weights)
    score = int(sum(dim * w for dim, w in weights) / total_weight) if total_weight > 0 else 0

    # --- Readiness gate ---
    readiness = _derive_readiness(
        completeness=completeness,
        validity=validity,
        attention=attention,
        policy=policy,
    )

    return HealthAssessmentRecord(
        revision=revision,
        score=score,
        readiness=readiness,
        dimensions={
            "completeness": completeness,
            "validity": validity,
            "confidence": confidence,
            "consistency": consistency,
            "specificity": specificity,
        },
        attention=attention,
        calculation_version=policy.calculation_version,
    )


def _needs_answered(
    output_needs: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    answers: dict[str, Any],
) -> dict[str, bool]:
    need_served: dict[str, bool] = {}
    for need in output_needs:
        need_id = need.get("id")
        if not isinstance(need_id, str):
            continue
        need_served[need_id] = False

    for question in questions:
        qid = question.get("id")
        if not isinstance(qid, str) or qid not in answers:
            continue
        for need_id in question.get("output_need_ids", []):
            if isinstance(need_id, str) and need_id in need_served:
                need_served[need_id] = True

    return need_served


def _heuristic_confidence(answers: dict[str, Any], questions: list[dict[str, Any]]) -> int:
    total = len([q for q in questions if isinstance(q.get("id"), str)])
    if total == 0:
        return 100
    answered = sum(1 for q in questions if isinstance(q.get("id"), str) and q["id"] in answers)
    return int(100 * answered / total)


def _rule_confidence(
    answers: dict[str, Any],
    questions: list[dict[str, Any]],
    output_needs: list[dict[str, Any]],
) -> tuple[int, list[AttentionItem]]:
    """Confidence: fraction of questions answered.

    Attention: for each required output need with zero answers among contributing
    questions, emit a ``weak_evidence`` info item (the unanswered-required-need
    blocking item is already produced by the completeness section, so this adds
    softer early-warning evidence items for optional needs too).
    """
    score = _heuristic_confidence(answers, questions)
    attention: list[AttentionItem] = []

    # Build a map: need_id → question IDs that serve it
    questions_by_need: dict[str, list[str]] = defaultdict(list)
    for q in questions:
        qid = q.get("id")
        if not isinstance(qid, str):
            continue
        for need_id in q.get("output_need_ids", []):
            if isinstance(need_id, str):
                questions_by_need[need_id].append(qid)

    for need in output_needs:
        need_id = need.get("id")
        if not isinstance(need_id, str):
            continue
        serving_questions = questions_by_need.get(need_id, [])
        answered_count = sum(1 for qid in serving_questions if qid in answers)
        if serving_questions and answered_count == 0:
            # No evidence at all for this need yet.
            attention.append(
                AttentionItem(
                    code="weak_evidence",
                    severity="info",
                    message=(
                        f"Output need {need_id!r} has no answers yet among "
                        f"{len(serving_questions)} contributing question(s)."
                    ),
                    recommended_action="Answer at least one of the associated questions.",
                    output_need_id=need_id,
                    evidence=[{"question_ids": serving_questions, "answered": answered_count}],
                )
            )
        elif len(serving_questions) > 1 and answered_count == 1:
            # Partially covered — thin evidence.
            attention.append(
                AttentionItem(
                    code="weak_evidence",
                    severity="info",
                    message=(
                        f"Output need {need_id!r} is served by {len(serving_questions)} "
                        "questions but only 1 has been answered; evidence is thin."
                    ),
                    recommended_action="Answer additional associated questions for stronger evidence.",
                    output_need_id=need_id,
                    evidence=[{"question_ids": serving_questions, "answered": answered_count}],
                )
            )

    return score, attention


def _rule_consistency(
    answers: dict[str, Any],
    questions: list[dict[str, Any]],
    output_needs: list[dict[str, Any]],
) -> tuple[int, list[AttentionItem]]:
    """Consistency: detect when two questions serving the same output need have
    conflicting scalar answers (i.e. non-null, differing values).

    Score = 100 unless contradictions are found, in which case it is reduced by
    25 per contradiction, floored at 0.
    """
    attention: list[AttentionItem] = []

    # Group answered questions by the needs they serve.
    answered_by_need: dict[str, list[tuple[str, Any]]] = defaultdict(list)
    for q in questions:
        qid = q.get("id")
        if not isinstance(qid, str) or qid not in answers:
            continue
        value = answers[qid]
        for need_id in q.get("output_need_ids", []):
            if isinstance(need_id, str):
                answered_by_need[need_id].append((qid, value))

    contradiction_count = 0
    for need in output_needs:
        need_id = need.get("id")
        if not isinstance(need_id, str):
            continue
        pairs = answered_by_need.get(need_id, [])
        # Look for any two entries where both are non-null scalars but differ.
        scalar_pairs = [
            (qid, v)
            for qid, v in pairs
            if v is not None and isinstance(v, (str, int, float, bool))
        ]
        if len(scalar_pairs) < 2:
            continue
        unique_values = {v for _, v in scalar_pairs}
        if len(unique_values) > 1:
            contradiction_count += 1
            question_ids = [qid for qid, _ in scalar_pairs]
            attention.append(
                AttentionItem(
                    code="contradiction",
                    severity="warning",
                    message=(
                        f"Output need {need_id!r} receives contradictory answers: "
                        f"{unique_values!r} from {question_ids}."
                    ),
                    recommended_action=(
                        "Review the conflicting answers and correct or remove the inconsistency."
                    ),
                    output_need_id=need_id,
                    evidence=[{"question_ids": question_ids, "values": list(unique_values)}],
                )
            )

    score = max(0, 100 - contradiction_count * 25)
    return score, attention


def _rule_specificity(
    answers: dict[str, Any],
    questions: list[dict[str, Any]],
) -> tuple[int, list[AttentionItem]]:
    """Specificity: fraction of non-empty answers.

    Attention: for each answered string question where the value is an empty
    string, emit an ``imprecision`` info item.
    """
    attention: list[AttentionItem] = []
    question_by_id = {q["id"]: q for q in questions if isinstance(q.get("id"), str)}
    if not answers:
        return 100, attention

    specific_count = 0
    for qid, value in answers.items():
        if value not in ("", None, [], {}):
            specific_count += 1
        else:
            question = question_by_id.get(qid)
            output_need_ids: list[str] = (
                [nid for nid in question.get("output_need_ids", []) if isinstance(nid, str)]
                if question is not None
                else []
            )
            attention.append(
                AttentionItem(
                    code="imprecision",
                    severity="info",
                    message=f"Answer for {qid!r} is empty or blank; a more specific value is expected.",
                    recommended_action=f"Provide a specific value for {qid!r}.",
                    output_need_id=output_need_ids[0] if output_need_ids else None,
                    evidence=[{"question_id": qid, "value": value}],
                )
            )

    total = len(answers)
    score = int(100 * specific_count / total) if total > 0 else 100
    return score, attention


def _derive_readiness(
    *,
    completeness: int,
    validity: int,
    attention: list[AttentionItem],
    policy: HealthPolicy,
) -> Readiness:
    if completeness < 100:
        return "not_ready"

    if validity < policy.minimum_validity:
        return "not_ready"

    blocking_attention = [a for a in attention if a.severity == policy.block_on]
    if blocking_attention:
        return "needs_attention"

    warning_attention = [a for a in attention if a.severity == "warning"]
    if warning_attention:
        return "needs_attention"

    return "ready"
