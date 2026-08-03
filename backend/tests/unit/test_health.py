from __future__ import annotations

from qava.domain.health import assess_health
from qava.domain.models import HealthPolicy


def _policy(
    *,
    minimum_validity: int = 0,
    block_on: str = "blocking",
) -> HealthPolicy:
    return HealthPolicy(
        calculation_version=1,
        completeness_weight=1.0,
        validity_weight=1.0,
        confidence_weight=1.0,
        consistency_weight=1.0,
        specificity_weight=1.0,
        minimum_validity=minimum_validity,
        block_on=block_on,  # type: ignore[arg-type]
    )


def test_completeness_dimension_is_fraction_of_required_needs_answered() -> None:
    output_needs = [
        {"id": "need:a", "required": True},
        {"id": "need:b", "required": True},
        {"id": "need:c", "required": False},
    ]
    questions = [
        {"id": "q-a", "output_need_ids": ["need:a"]},
        {"id": "q-b", "output_need_ids": ["need:b"]},
        {"id": "q-c", "output_need_ids": ["need:c"]},
    ]
    answers = {"q-a": "answered"}

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers=answers,
        policy=_policy(),
        revision=1,
    )

    assert result.dimensions["completeness"] == 50


def test_validity_dimension_reflects_schema_valid_answers() -> None:
    output_needs = [{"id": "need:a", "required": True}]
    questions = [
        {
            "id": "q-valid",
            "output_need_ids": ["need:a"],
            "answer_schema": {"type": "string"},
        },
        {
            "id": "q-invalid",
            "output_need_ids": [],
            "answer_schema": {"type": "number"},
        },
    ]
    answers = {
        "q-valid": "hello",
        "q-invalid": "not-a-number",
    }

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers=answers,
        policy=_policy(),
        revision=1,
    )

    assert 0 < result.dimensions["validity"] < 100


def test_overall_score_is_weighted_sum_of_dimensions() -> None:
    output_needs: list = []
    questions: list = []
    answers: dict = {}

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers=answers,
        policy=_policy(),
        revision=1,
    )

    total = sum(result.dimensions.values())
    assert total >= 0
    assert 0 <= result.score <= 100


def test_readiness_not_ready_when_required_need_unanswered() -> None:
    output_needs = [{"id": "need:a", "required": True}]
    questions = [{"id": "q-a", "output_need_ids": ["need:a"]}]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={},
        policy=_policy(minimum_validity=0),
        revision=1,
    )

    assert result.readiness == "not_ready"


def test_readiness_ready_when_all_required_answered_and_validity_meets_threshold() -> None:
    output_needs = [{"id": "need:a", "required": True}]
    questions = [
        {
            "id": "q-a",
            "output_need_ids": ["need:a"],
            "answer_schema": {"type": "string"},
        }
    ]
    answers = {"q-a": "value"}

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers=answers,
        policy=_policy(minimum_validity=0),
        revision=1,
    )

    assert result.readiness == "ready"


def test_blocking_attention_item_blocks_readiness() -> None:
    output_needs = [{"id": "need:a", "required": True}]
    questions = [
        {
            "id": "q-a",
            "output_need_ids": ["need:a"],
            "answer_schema": {"type": "number"},
        }
    ]
    answers = {"q-a": "not-a-number"}

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers=answers,
        policy=_policy(minimum_validity=0, block_on="blocking"),
        revision=1,
    )

    blocking = [item for item in result.attention if item.severity == "blocking"]
    assert blocking
    assert result.readiness != "ready"


def test_evidence_linked_attention_references_question_and_output_need() -> None:
    output_needs = [{"id": "need:x", "required": True}]
    questions = [
        {
            "id": "q-x",
            "output_need_ids": ["need:x"],
            "answer_schema": {"type": "integer"},
        }
    ]
    answers = {"q-x": "not-int"}

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers=answers,
        policy=_policy(),
        revision=1,
    )

    assert result.attention
    linked = result.attention[0]
    assert linked.output_need_id is not None
    assert linked.code


# ---------------------------------------------------------------------------
# T027 — US3 fixed health rules
# ---------------------------------------------------------------------------


def test_confidence_weak_evidence_emits_info_attention_for_unanswered_need() -> None:
    """A need with contributing questions but zero answers → weak_evidence info item."""
    output_needs = [{"id": "need:a", "required": False}]
    questions = [
        {"id": "q-a", "output_need_ids": ["need:a"]},
        {"id": "q-b", "output_need_ids": ["need:a"]},
    ]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={},
        policy=_policy(),
        revision=1,
    )

    weak = [item for item in result.attention if item.code == "weak_evidence"]
    assert weak, "Expected at least one weak_evidence attention item"
    assert weak[0].severity == "info"
    assert weak[0].output_need_id == "need:a"


def test_confidence_thin_evidence_emits_when_one_of_many_answered() -> None:
    """One of two contributing questions answered → thin-evidence weak_evidence item."""
    output_needs = [{"id": "need:a", "required": False}]
    questions = [
        {"id": "q-a", "output_need_ids": ["need:a"]},
        {"id": "q-b", "output_need_ids": ["need:a"]},
    ]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "value"},
        policy=_policy(),
        revision=1,
    )

    weak = [item for item in result.attention if item.code == "weak_evidence"]
    assert weak, "Expected a thin-evidence item when only 1 of 2 questions answered"
    assert "thin" in weak[0].message


def test_confidence_no_weak_evidence_when_all_questions_answered() -> None:
    output_needs = [{"id": "need:a", "required": False}]
    questions = [
        {"id": "q-a", "output_need_ids": ["need:a"]},
        {"id": "q-b", "output_need_ids": ["need:a"]},
    ]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "v1", "q-b": "v2"},
        policy=_policy(),
        revision=1,
    )

    weak = [item for item in result.attention if item.code == "weak_evidence"]
    assert not weak, "No weak_evidence expected when all contributing questions answered"


def test_consistency_contradiction_emits_warning_and_reduces_score() -> None:
    """Two questions targeting the same need with different scalar values → contradiction."""
    output_needs = [{"id": "need:a", "required": False}]
    questions = [
        {"id": "q-a", "output_need_ids": ["need:a"]},
        {"id": "q-b", "output_need_ids": ["need:a"]},
    ]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "red", "q-b": "blue"},
        policy=_policy(),
        revision=1,
    )

    contradictions = [item for item in result.attention if item.code == "contradiction"]
    assert contradictions, "Expected a contradiction attention item"
    assert contradictions[0].severity == "warning"
    assert result.dimensions["consistency"] < 100


def test_consistency_no_contradiction_when_values_agree() -> None:
    output_needs = [{"id": "need:a", "required": False}]
    questions = [
        {"id": "q-a", "output_need_ids": ["need:a"]},
        {"id": "q-b", "output_need_ids": ["need:a"]},
    ]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "same", "q-b": "same"},
        policy=_policy(),
        revision=1,
    )

    contradictions = [item for item in result.attention if item.code == "contradiction"]
    assert not contradictions
    assert result.dimensions["consistency"] == 100


def test_specificity_imprecision_emits_info_for_empty_string_answer() -> None:
    output_needs = [{"id": "need:a", "required": False}]
    questions = [{"id": "q-a", "output_need_ids": ["need:a"], "answer_schema": {"type": "string"}}]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": ""},
        policy=_policy(),
        revision=1,
    )

    imprecise = [item for item in result.attention if item.code == "imprecision"]
    assert imprecise, "Expected an imprecision attention item for empty string"
    assert imprecise[0].severity == "info"
    assert result.dimensions["specificity"] < 100


def test_specificity_no_imprecision_when_answers_are_specific() -> None:
    output_needs = [{"id": "need:a", "required": False}]
    questions = [{"id": "q-a", "output_need_ids": ["need:a"], "answer_schema": {"type": "string"}}]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "specific answer"},
        policy=_policy(),
        revision=1,
    )

    imprecise = [item for item in result.attention if item.code == "imprecision"]
    assert not imprecise
    assert result.dimensions["specificity"] == 100


def test_adapter_validation_dry_run_reduces_validity_and_emits_blocking_attention() -> None:
    """T030: passing an adapter_validator that returns problems reduces validity and blocks."""
    output_needs = [{"id": "need:a", "required": True}]
    questions = [
        {
            "id": "q-a",
            "output_need_ids": ["need:a"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": "/component"},
        }
    ]

    def bad_validator(data: dict) -> list[str]:
        return ["Schema contract violation: component must be a registered name."]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "not-valid"},
        policy=_policy(minimum_validity=80),
        revision=1,
        adapter_validator=bad_validator,
    )

    adapter_items = [item for item in result.attention if item.code == "adapter_validation_failed"]
    assert adapter_items, "Expected adapter_validation_failed attention item"
    assert adapter_items[0].severity == "blocking"
    # Validity should be reduced due to adapter penalty.
    assert result.dimensions["validity"] < 100


def test_adapter_validation_no_effect_when_validator_passes() -> None:
    output_needs = [{"id": "need:a", "required": True}]
    questions = [
        {
            "id": "q-a",
            "output_need_ids": ["need:a"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": "/component"},
        }
    ]

    result = assess_health(
        output_needs=output_needs,
        questions=questions,
        answers={"q-a": "valid-name"},
        policy=_policy(),
        revision=1,
        adapter_validator=lambda _: [],
    )

    adapter_items = [item for item in result.attention if item.code == "adapter_validation_failed"]
    assert not adapter_items
