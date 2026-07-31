from __future__ import annotations

from qava.domain.answers import validate_answer
from qava.domain.components import infer_component, is_component_compatible
from qava.domain.conditions import evaluate_condition


def test_validate_answer_enforces_json_schema_and_choice_ids() -> None:
    question = {
        "answer_schema": {"type": "string"},
        "choices": [
            {"id": "budget-low", "label": "Under 500k"},
            {"id": "budget-high", "label": "Over 500k"},
        ],
    }

    assert validate_answer(question, "budget-low") == []

    issues = validate_answer(question, "Under 500k")
    assert issues
    assert "choice_id" in issues[0]


def test_evaluate_condition_supports_equals_contains_exists() -> None:
    answers = {
        "q-style": "modern",
        "q-features": ["deck", "pool"],
        "q-notes": "south-facing lot",
        "q-null": None,
    }

    assert evaluate_condition(
        {"source_question_id": "q-style", "operator": "equals", "value": "modern"},
        answers,
    )
    assert not evaluate_condition(
        {"source_question_id": "q-style", "operator": "equals", "value": 1},
        answers,
    )

    assert evaluate_condition(
        {"source_question_id": "q-features", "operator": "contains", "value": "deck"},
        answers,
    )
    assert evaluate_condition(
        {"source_question_id": "q-notes", "operator": "contains", "value": "facing"},
        answers,
    )
    assert not evaluate_condition(
        {"source_question_id": "q-features", "operator": "contains", "value": "garage"},
        answers,
    )

    assert evaluate_condition({"source_question_id": "q-style", "operator": "exists"}, answers)
    assert not evaluate_condition({"source_question_id": "q-null", "operator": "exists"}, answers)
    assert not evaluate_condition(
        {"source_question_id": "q-missing", "operator": "exists"},
        answers,
    )


def test_component_compatibility_and_fallback_resolution() -> None:
    catalog = {
        "components": [
            {"name": "short_text", "answer_shape": "string"},
            {"name": "single_select", "answer_shape": "scalar"},
            {"name": "multi_select", "answer_shape": "array"},
        ]
    }

    string_schema = {"type": "string"}
    array_schema = {"type": "array", "items": {"type": "string"}}

    assert is_component_compatible("short_text", string_schema, catalog)
    assert is_component_compatible("single_select", string_schema, catalog)
    assert not is_component_compatible("short_text", array_schema, catalog)

    # Falls back when declared renderer is incompatible.
    resolved = infer_component(
        answer_schema=array_schema,
        catalog=catalog,
        preferred_component="short_text",
        fallback_component="multi_select",
    )
    assert resolved == "multi_select"
