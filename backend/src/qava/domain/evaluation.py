"""Pure deterministic session evaluation.

``evaluate_session`` is the single rule set for all session reads and mutations.
It accepts immutable inputs and returns an immutable ``SessionEvaluation``;
it performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qava.domain.conditions import evaluate_condition
from qava.domain.health import assess_health
from qava.domain.models import (
    HealthAssessmentRecord,
    NavigationFocus,
    PublishedQuestionnaireRecord,
    SessionRecord,
)
from qava.domain.projection import project_result, ProjectionResult


@dataclass(frozen=True)
class Progress:
    satisfied_required: int
    total_required: int


@dataclass(frozen=True)
class SessionEvaluation:
    """Complete deterministic evaluation of one session snapshot."""

    applicable_question_ids: frozenset[str]
    """Questions whose applicability condition is satisfied given current answers."""

    active_answer_ids: frozenset[str]
    """Applicable questions that have an accepted answer."""

    active_skip_ids: frozenset[str]
    """Applicable questions with a persisted skip disposition and no answer."""

    current_interaction: dict[str, Any] | None
    """Navigation-focus question if still eligible; else deterministic next."""

    projection: ProjectionResult

    unresolved_needs: list[dict[str, Any]]
    """Output needs not satisfied by any active answer."""

    progress: Progress

    health: HealthAssessmentRecord

    permitted_actions: list[str]


def evaluate_session(
    questionnaire: PublishedQuestionnaireRecord,
    session: SessionRecord,
) -> SessionEvaluation:
    """Return the complete deterministic evaluation for *session*.

    This is the sole rule set consumed by all reads and post-mutation responses.
    """
    questions = questionnaire.questions
    answers = dict(session.answers)

    # --- Step 1: applicable question IDs ---
    applicable_ids: set[str] = set()
    for q in questions:
        qid = q.get("id")
        if not isinstance(qid, str):
            continue
        if evaluate_condition(q.get("applicability"), answers):
            applicable_ids.add(qid)

    # --- Step 2: active answers (applicable + has answer) ---
    active_answer_ids = frozenset(
        qid for qid in applicable_ids if qid in answers
    )

    # --- Step 3: active skips (applicable + disposition present + no answer) ---
    skip_dispositions = session.skip_dispositions
    active_skip_ids = frozenset(
        qid
        for qid in applicable_ids
        if qid in skip_dispositions and qid not in answers
    )

    # --- Step 4: active answers dict for downstream (only applicable answers) ---
    active_answers = {qid: answers[qid] for qid in active_answer_ids}

    # --- Step 5: projection over active answers only ---
    projection = project_result(questions=questions, answers=active_answers)

    # --- Step 6: unresolved output needs ---
    unresolved = _compute_unresolved_needs(
        questionnaire.output_needs, questions, active_answer_ids
    )

    # --- Step 7: progress ---
    required_needs = [n for n in questionnaire.output_needs if n.get("required")]
    unresolved_required_count = sum(1 for n in unresolved if n.get("required"))
    progress = Progress(
        satisfied_required=len(required_needs) - unresolved_required_count,
        total_required=len(required_needs),
    )

    # --- Step 8: health over active answers ---
    health = assess_health(
        output_needs=questionnaire.output_needs,
        questions=questions,
        answers=active_answers,
        policy=questionnaire.health_policy,
        revision=session.revision,
    )

    # --- Step 9: current interaction ---
    current_interaction = _resolve_current_interaction(
        questions=questions,
        applicable_ids=applicable_ids,
        active_answer_ids=active_answer_ids,
        active_skip_ids=active_skip_ids,
        navigation_focus=session.navigation_focus,
    )

    # --- Step 10: permitted actions ---
    permitted_actions = _derive_permitted_actions(
        current_interaction=current_interaction,
        health=health,
        active_skip_ids=active_skip_ids,
        unresolved=unresolved,
    )

    return SessionEvaluation(
        applicable_question_ids=frozenset(applicable_ids),
        active_answer_ids=active_answer_ids,
        active_skip_ids=active_skip_ids,
        current_interaction=current_interaction,
        projection=projection,
        unresolved_needs=unresolved,
        progress=progress,
        health=health,
        permitted_actions=permitted_actions,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _resolve_current_interaction(
    *,
    questions: list[dict[str, Any]],
    applicable_ids: set[str],
    active_answer_ids: frozenset[str],
    active_skip_ids: frozenset[str],
    navigation_focus: NavigationFocus | None,
) -> dict[str, Any] | None:
    """Return the current interaction, honouring navigation focus when still eligible."""
    question_by_id = {q["id"]: q for q in questions if isinstance(q.get("id"), str)}

    # Honour navigation focus if the target is still eligible (applicable, unanswered, unskipped)
    if navigation_focus is not None:
        fq = question_by_id.get(navigation_focus.question_id)
        if (
            fq is not None
            and navigation_focus.question_id in applicable_ids
            and navigation_focus.question_id not in active_answer_ids
            and navigation_focus.question_id not in active_skip_ids
        ):
            return _to_interaction_dict(fq)

    # Deterministic selection: required first, then optional; both by ascending order
    required: list[tuple[int, dict[str, Any]]] = []
    optional: list[tuple[int, dict[str, Any]]] = []
    for q in questions:
        qid = q.get("id")
        if not isinstance(qid, str):
            continue
        if qid not in applicable_ids:
            continue
        if qid in active_answer_ids or qid in active_skip_ids:
            continue
        order = q.get("order", 0) or 0
        if q.get("required"):
            required.append((order, q))
        else:
            optional.append((order, q))

    if required:
        return _to_interaction_dict(sorted(required, key=lambda x: x[0])[0][1])
    if optional:
        return _to_interaction_dict(sorted(optional, key=lambda x: x[0])[0][1])
    return None


def _to_interaction_dict(question: dict[str, Any]) -> dict[str, Any]:
    presentation = question.get("presentation") or {}
    component = {
        "name": presentation.get("name", "short_text"),
        "version": presentation.get("version", 1),
        "props": presentation.get("props", {}),
    }
    return {
        "id": question["id"],
        "kind": "question",
        "output_need_ids": question.get("output_need_ids", []),
        "prompt": question.get("prompt", ""),
        "reason": question.get("reason", "Collect evidence for the output contract."),
        "required": bool(question.get("required", False)),
        "answer_schema": question.get("answer_schema", {}),
        "component": component,
        "policy_limit": None,
        "choices": question.get("choices"),
        "option_source": question.get("option_source"),
    }


def _compute_unresolved_needs(
    output_needs: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    active_answer_ids: frozenset[str],
) -> list[dict[str, Any]]:
    served: set[str] = set()
    for q in questions:
        qid = q.get("id")
        if isinstance(qid, str) and qid in active_answer_ids:
            for need_id in q.get("output_need_ids", []):
                if isinstance(need_id, str):
                    served.add(need_id)

    unresolved: list[dict[str, Any]] = []
    for need in output_needs:
        need_id = need.get("id")
        if not isinstance(need_id, str) or need_id in served:
            continue
        question = next(
            (q for q in questions if need_id in q.get("output_need_ids", [])),
            None,
        )
        if question is None:
            continue
        question_id = question.get("id")
        if not isinstance(question_id, str):
            continue
        unresolved.append(
            {
                "id": need_id,
                "target": need.get("target"),
                "label": need.get("label"),
                "required": need.get("required", False),
                "criticality": need.get("criticality", "normal"),
                "question_id": question_id,
                "topic_id": question.get("topic_id"),
            }
        )
    return unresolved


def _derive_permitted_actions(
    *,
    current_interaction: dict[str, Any] | None,
    health: HealthAssessmentRecord,
    active_skip_ids: frozenset[str],
    unresolved: list[dict[str, Any]],
) -> list[str]:
    actions: list[str] = ["save_and_exit", "delete"]
    if current_interaction is not None:
        actions.append("answer")
        current_id = current_interaction.get("id", "")
        is_required = current_interaction.get("required", False)
        already_skipped = current_id in active_skip_ids
        if not is_required and not already_skipped:
            actions.append("skip")
    if unresolved:
        actions.append("navigate")
    if health.readiness == "ready":
        actions.extend(["preview_publication", "publish"])
    return actions
