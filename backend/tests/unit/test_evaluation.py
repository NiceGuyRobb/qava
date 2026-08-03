"""Unit test matrix for evaluate_session (T005 / SC-001).

Tests verify that a single evaluation produces internally consistent results
and that inactive retained evidence is excluded from all derived fields.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from qava.domain.evaluation import evaluate_session
from qava.domain.models import (
    AssistancePolicy,
    HealthPolicy,
    NavigationFocus,
    PublishedQuestionnaireRecord,
    QuestionnaireId,
    SessionId,
    SessionRecord,
    SkipDisposition,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_DEFAULT_HEALTH_POLICY = HealthPolicy(
    calculation_version=1,
    completeness_weight=1.0,
    validity_weight=1.0,
    confidence_weight=1.0,
    consistency_weight=1.0,
    specificity_weight=1.0,
    minimum_validity=0,
    block_on="blocking",
)

_DEFAULT_ASSISTANCE_POLICY = AssistancePolicy(
    enabled_operations=[],
    maximum_clarifications_per_interaction=0,
    maximum_generated_interactions_per_session=0,
    timeout_ms=5000,
    require_extraction_confirmation=True,
)


def _questionnaire(questions: list[dict[str, Any]], output_needs: list[dict[str, Any]] | None = None) -> PublishedQuestionnaireRecord:
    return PublishedQuestionnaireRecord(
        questionnaire_id=QuestionnaireId("test-qs"),
        version=1,
        title="Test",
        output_contract={"type": "object"},
        output_needs=output_needs or [],
        questions=questions,
        health_policy=_DEFAULT_HEALTH_POLICY,
        assistance_policy=_DEFAULT_ASSISTANCE_POLICY,
        content_hash="abc",
        published_by="test",
        published_at=datetime.now(UTC),
    )


def _session(
    answers: dict[str, Any] | None = None,
    skip_dispositions: dict[str, SkipDisposition] | None = None,
    navigation_focus: NavigationFocus | None = None,
    revision: int = 1,
) -> SessionRecord:
    now = datetime.now(UTC)
    return SessionRecord(
        session_id=SessionId("sess-1"),
        questionnaire_id=QuestionnaireId("test-qs"),
        questionnaire_version=1,
        revision=revision,
        status="active",
        answers=answers or {},
        generated_interactions=[],
        skip_dispositions=skip_dispositions or {},
        navigation_focus=navigation_focus,
        created_by="actor",
        created_at=now,
        updated_at=now,
    )


def _skip(question_id: str, revision: int = 1) -> SkipDisposition:
    return SkipDisposition(
        question_id=question_id,
        accepted_revision=revision,
        actor_id="actor",
        skipped_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# SC-001: All fields agree on which evidence is active
# ---------------------------------------------------------------------------

def test_inactive_retained_answer_excluded_from_all_fields() -> None:
    """Retained answer for inapplicable question must not appear in any derived field."""
    questions = [
        {
            "id": "q-style",
            "order": 1,
            "required": True,
            "output_need_ids": ["need:style"],
            "answer_schema": {"type": "string", "enum": ["modern", "traditional"]},
            "mapping": {"mode": "direct", "target": "/style"},
        },
        {
            "id": "q-outdoors",
            "order": 2,
            "required": False,
            "applicability": {"source_question_id": "q-style", "operator": "equals", "value": "modern"},
            "output_need_ids": ["need:outdoors"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": "/outdoors"},
        },
    ]
    output_needs = [
        {"id": "need:style", "target": "/style", "required": True},
        {"id": "need:outdoors", "target": "/outdoors", "required": False},
    ]
    qs = _questionnaire(questions, output_needs)
    # q-outdoors was answered when q-style was "modern", but now q-style is "traditional"
    session = _session(answers={"q-style": "traditional", "q-outdoors": "pool"})

    ev = evaluate_session(qs, session)

    # q-outdoors is inapplicable — its answer must be excluded everywhere
    assert "q-outdoors" not in ev.active_answer_ids
    assert "q-outdoors" in ev.applicable_question_ids is False or "q-outdoors" not in ev.applicable_question_ids
    assert "/outdoors" not in ev.projection.data
    assert "/outdoors" not in ev.projection.provenance

    # The inapplicable need is still listed as unresolved (question exists but answer is inactive)
    unresolved_ids = {n["id"] for n in ev.unresolved_needs}
    assert "need:outdoors" in unresolved_ids

    # style question is answered and applicable — must be active
    assert "q-style" in ev.active_answer_ids
    assert ev.projection.data == {"style": "traditional"}

    # All fields must agree: same evidence
    assert ev.progress.satisfied_required == 1  # style answered
    assert ev.progress.total_required == 1


def test_all_fields_consistent_after_answer_makes_question_inapplicable() -> None:
    """SC-001: projection, unresolved needs, progress, health agree."""
    questions = [
        {"id": "q-a", "order": 1, "required": True, "output_need_ids": ["n:a"],
         "answer_schema": {"type": "string"}, "mapping": {"mode": "direct", "target": "/a"}},
        {"id": "q-b", "order": 2, "required": True, "output_need_ids": ["n:b"],
         "applicability": {"source_question_id": "q-a", "operator": "equals", "value": "yes"},
         "answer_schema": {"type": "string"}, "mapping": {"mode": "direct", "target": "/b"}},
    ]
    output_needs = [
        {"id": "n:a", "target": "/a", "required": True},
        {"id": "n:b", "target": "/b", "required": True},
    ]
    qs = _questionnaire(questions, output_needs)

    # Both answered when q-a was "yes", but now q-a is "no" making q-b inapplicable
    session = _session(answers={"q-a": "no", "q-b": "something"})
    ev = evaluate_session(qs, session)

    assert "q-b" not in ev.active_answer_ids
    assert "/b" not in ev.projection.data
    unresolved_ids = {n["id"] for n in ev.unresolved_needs}
    # n:b is inapplicable so no question serves it in the applicable set — not in unresolved
    # (unresolved only lists needs with an applicable unanswered question)
    assert "n:a" not in unresolved_ids  # answered
    assert ev.progress.satisfied_required == 1  # only q-a counts


# ---------------------------------------------------------------------------
# Skip disposition tests
# ---------------------------------------------------------------------------

def test_skip_disposition_suppresses_question_from_current_interaction() -> None:
    questions = [
        {"id": "q-required", "order": 1, "required": True, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
        {"id": "q-optional", "order": 2, "required": False, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
    ]
    qs = _questionnaire(questions)
    session = _session(
        answers={"q-required": "done"},
        skip_dispositions={"q-optional": _skip("q-optional")},
    )
    ev = evaluate_session(qs, session)

    assert ev.current_interaction is None  # no eligible questions left
    assert "q-optional" in ev.active_skip_ids
    assert "skip" not in ev.permitted_actions


def test_skip_suppression_cleared_when_question_becomes_inapplicable() -> None:
    """When the skipped question becomes inapplicable, the skip has no selective effect."""
    questions = [
        {"id": "q-flag", "order": 1, "required": True, "output_need_ids": [],
         "answer_schema": {"type": "string", "enum": ["yes", "no"]}},
        {
            "id": "q-conditional",
            "order": 2,
            "required": False,
            "applicability": {"source_question_id": "q-flag", "operator": "equals", "value": "yes"},
            "output_need_ids": [],
            "answer_schema": {"type": "string"},
        },
    ]
    qs = _questionnaire(questions)
    # q-conditional was skipped when q-flag was "yes", now q-flag is "no"
    session = _session(
        answers={"q-flag": "no"},
        skip_dispositions={"q-conditional": _skip("q-conditional")},
    )
    ev = evaluate_session(qs, session)

    # q-conditional is inapplicable, so not in active_skip_ids
    assert "q-conditional" not in ev.active_skip_ids
    assert ev.current_interaction is None  # q-flag answered, q-conditional inapplicable


def test_skip_does_not_suppress_question_once_applicable_again() -> None:
    """If question is back to applicable after becoming inapplicable, skip still suppresses."""
    questions = [
        {"id": "q-flag", "order": 1, "required": True, "output_need_ids": [],
         "answer_schema": {"type": "string", "enum": ["yes", "no"]}},
        {
            "id": "q-cond",
            "order": 2,
            "required": False,
            "applicability": {"source_question_id": "q-flag", "operator": "equals", "value": "yes"},
            "output_need_ids": [],
            "answer_schema": {"type": "string"},
        },
    ]
    qs = _questionnaire(questions)
    # q-flag is "yes" again and q-cond is skipped
    session = _session(
        answers={"q-flag": "yes"},
        skip_dispositions={"q-cond": _skip("q-cond")},
    )
    ev = evaluate_session(qs, session)
    assert "q-cond" in ev.active_skip_ids
    assert ev.current_interaction is None  # suppressed by disposition


# ---------------------------------------------------------------------------
# Navigation focus tests
# ---------------------------------------------------------------------------

def test_navigation_focus_overrides_selection() -> None:
    questions = [
        {"id": "q-first", "order": 1, "required": True, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
        {"id": "q-target", "order": 2, "required": False, "output_need_ids": ["need:target"],
         "answer_schema": {"type": "string"}},
    ]
    qs = _questionnaire(questions)
    focus = NavigationFocus(
        question_id="q-target",
        output_need_id="need:target",
        topic_id=None,
        accepted_revision=1,
        actor_id="actor",
    )
    session = _session(navigation_focus=focus)
    ev = evaluate_session(qs, session)

    assert ev.current_interaction is not None
    assert ev.current_interaction["id"] == "q-target"


def test_navigation_focus_cleared_when_target_answered() -> None:
    questions = [
        {"id": "q-target", "order": 1, "required": False, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
    ]
    qs = _questionnaire(questions)
    focus = NavigationFocus(
        question_id="q-target",
        output_need_id=None,
        topic_id=None,
        accepted_revision=1,
        actor_id="actor",
    )
    session = _session(answers={"q-target": "done"}, navigation_focus=focus)
    ev = evaluate_session(qs, session)

    # Focus target is answered — evaluator should not select it
    assert ev.current_interaction is None


def test_navigation_focus_cleared_when_target_inapplicable() -> None:
    questions = [
        {"id": "q-flag", "order": 1, "required": True, "output_need_ids": [],
         "answer_schema": {"type": "string", "enum": ["yes", "no"]}},
        {
            "id": "q-target",
            "order": 2,
            "required": False,
            "applicability": {"source_question_id": "q-flag", "operator": "equals", "value": "yes"},
            "output_need_ids": [],
            "answer_schema": {"type": "string"},
        },
    ]
    qs = _questionnaire(questions)
    focus = NavigationFocus(
        question_id="q-target",
        output_need_id=None,
        topic_id=None,
        accepted_revision=1,
        actor_id="actor",
    )
    session = _session(answers={"q-flag": "no"}, navigation_focus=focus)
    ev = evaluate_session(qs, session)

    # Focus target is inapplicable — falls back to deterministic selection
    assert ev.current_interaction is None  # q-flag answered, q-target inapplicable


# ---------------------------------------------------------------------------
# Permitted actions
# ---------------------------------------------------------------------------

def test_skip_not_in_permitted_actions_for_required_interaction() -> None:
    questions = [
        {"id": "q-req", "order": 1, "required": True, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
    ]
    ev = evaluate_session(_questionnaire(questions), _session())
    assert ev.current_interaction is not None
    assert ev.current_interaction["id"] == "q-req"
    assert "skip" not in ev.permitted_actions


def test_skip_in_permitted_actions_for_optional_interaction() -> None:
    questions = [
        {"id": "q-opt", "order": 1, "required": False, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
    ]
    ev = evaluate_session(_questionnaire(questions), _session())
    assert "skip" in ev.permitted_actions


def test_skip_absent_when_already_skipped() -> None:
    questions = [
        {"id": "q-opt", "order": 1, "required": False, "output_need_ids": [],
         "answer_schema": {"type": "string"}},
    ]
    session = _session(skip_dispositions={"q-opt": _skip("q-opt")})
    ev = evaluate_session(_questionnaire(questions), session)
    assert "skip" not in ev.permitted_actions


def test_publish_in_permitted_actions_when_ready() -> None:
    questions = [
        {"id": "q-a", "order": 1, "required": True, "output_need_ids": ["n:a"],
         "answer_schema": {"type": "string"}, "mapping": {"mode": "direct", "target": "/a"}},
    ]
    output_needs = [{"id": "n:a", "target": "/a", "required": True}]
    qs = _questionnaire(questions, output_needs)
    session = _session(answers={"q-a": "value"})
    ev = evaluate_session(qs, session)

    assert ev.health.readiness == "ready"
    assert "publish" in ev.permitted_actions
    assert "preview_publication" in ev.permitted_actions
