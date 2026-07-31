from __future__ import annotations

from qava.domain.selection import select_next_interaction


def _questions() -> list[dict]:
    return [
        {
            "id": "q-style",
            "order": 1,
            "required": True,
            "output_need_ids": ["need:preferences/style"],
        },
        {
            "id": "q-budget",
            "order": 2,
            "required": True,
            "output_need_ids": ["need:budget/range"],
        },
        {
            "id": "q-outdoors",
            "order": 3,
            "required": False,
            "applicability": {
                "source_question_id": "q-style",
                "operator": "equals",
                "value": "modern",
            },
            "output_need_ids": ["need:preferences/outdoors"],
        },
        {
            "id": "q-rooms",
            "order": 4,
            "required": False,
            "output_need_ids": ["need:rooms"],
        },
    ]


def test_first_unanswered_required_question_is_selected_first() -> None:
    result = select_next_interaction(
        questions=_questions(),
        answers={},
    )
    assert result is not None
    assert result["question_id"] == "q-style"


def test_inapplicable_question_is_skipped() -> None:
    # q-style answered as "traditional" so q-outdoors condition is False
    result = select_next_interaction(
        questions=_questions(),
        answers={"q-style": "traditional"},
    )
    assert result is not None
    assert result["question_id"] == "q-budget"


def test_all_required_answered_selects_optional_in_order() -> None:
    answers = {
        "q-style": "modern",
        "q-budget": "600000_900000",
    }
    result = select_next_interaction(
        questions=_questions(),
        answers=answers,
    )
    assert result is not None
    assert result["question_id"] == "q-outdoors"


def test_all_applicable_questions_answered_returns_none() -> None:
    answers = {
        "q-style": "traditional",
        "q-budget": "600000_900000",
        "q-rooms": "3",
    }
    result = select_next_interaction(
        questions=_questions(),
        answers=answers,
    )
    assert result is None


def test_required_unanswered_takes_priority_over_optional() -> None:
    answers = {"q-style": "modern"}
    result = select_next_interaction(
        questions=_questions(),
        answers=answers,
    )
    assert result is not None
    assert result["question_id"] == "q-budget"


def test_tie_break_uses_declared_order_field() -> None:
    questions = [
        {"id": "q-b", "order": 2, "required": True, "output_need_ids": []},
        {"id": "q-a", "order": 1, "required": True, "output_need_ids": []},
    ]
    result = select_next_interaction(questions=questions, answers={})
    assert result is not None
    assert result["question_id"] == "q-a"
