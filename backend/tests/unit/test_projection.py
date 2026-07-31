from __future__ import annotations

from qava.domain.projection import project_result


def test_nested_collection_compose_builds_typed_array_with_provenance() -> None:
    questions = [
        {"id": "q-a-name", "mapping": {"mode": "direct", "target": "/tmp/a_name"}},
        {"id": "q-a-area", "mapping": {"mode": "direct", "target": "/tmp/a_area"}},
        {"id": "q-b-name", "mapping": {"mode": "direct", "target": "/tmp/b_name"}},
        {
            "id": "q-rooms",
            "mapping": {
                "mode": "compose",
                "target": "/rooms",
                "shape": "array",
                "sources": [
                    {
                        "shape": "object",
                        "sources": {"name": "q-a-name", "area": "q-a-area"},
                    },
                    {"shape": "object", "sources": {"name": "q-b-name"}},
                ],
            },
        },
    ]
    answers = {"q-a-name": "Kitchen", "q-a-area": 200, "q-b-name": "Bath"}

    projection = project_result(questions=questions, answers=answers)

    assert projection.data["rooms"] == [
        {"name": "Kitchen", "area": 200},
        {"name": "Bath"},
    ]
    assert projection.provenance["/rooms"]["question_ids"] == [
        "q-a-name",
        "q-a-area",
        "q-b-name",
    ]


def test_nested_compose_respects_max_depth() -> None:
    # A mapping nested deeper than MAX_COMPOSE_DEPTH resolves to nothing.
    deep: dict = {"shape": "object", "sources": {"leaf": "q-leaf"}}
    for _ in range(5):
        deep = {"shape": "object", "sources": {"nested": deep}}
    questions = [
        {"id": "q-leaf", "mapping": {"mode": "direct", "target": "/tmp/leaf"}},
        {"id": "q-deep", "mapping": {"mode": "compose", "target": "/deep", **deep}},
    ]
    projection = project_result(questions=questions, answers={"q-leaf": "value"})
    assert "deep" not in projection.data


def test_direct_and_compose_projection_and_provenance() -> None:
    questions = [
        {
            "id": "q-budget",
            "mapping": {"mode": "direct", "target": "/budget/range"},
        },
        {
            "id": "q-funding",
            "mapping": {"mode": "direct", "target": "/budget/funding"},
        },
        {
            "id": "q-structure",
            "mapping": {
                "mode": "compose",
                "target": "/structure/target_area",
                "shape": "object",
                "sources": {
                    "value": "q-area-value",
                    "unit": "q-area-unit",
                },
            },
        },
        {"id": "q-area-value", "mapping": {"mode": "direct", "target": "/tmp/area_value"}},
        {"id": "q-area-unit", "mapping": {"mode": "direct", "target": "/tmp/area_unit"}},
    ]

    answers = {
        "q-budget": "600000_900000",
        "q-funding": "Construction loan",
        "q-area-value": 3200,
        "q-area-unit": "sq_ft",
    }

    projection = project_result(questions=questions, answers=answers)

    assert projection.data["budget"]["range"] == "600000_900000"
    assert projection.data["budget"]["funding"] == "Construction loan"
    assert projection.data["structure"]["target_area"] == {"value": 3200, "unit": "sq_ft"}

    assert projection.provenance["/budget/range"]["question_ids"] == ["q-budget"]
    assert projection.provenance["/structure/target_area"]["question_ids"] == [
        "q-area-value",
        "q-area-unit",
    ]


def test_changed_paths_and_inactive_answer_removal() -> None:
    questions = [
        {
            "id": "q-style",
            "mapping": {"mode": "direct", "target": "/preferences/style"},
        },
        {
            "id": "q-outdoors",
            "applicability": {
                "source_question_id": "q-style",
                "operator": "equals",
                "value": "modern",
            },
            "mapping": {"mode": "direct", "target": "/preferences/outdoors"},
        },
    ]

    answers = {
        "q-style": "traditional",
        "q-outdoors": "pool",
    }
    previous_data = {
        "preferences": {
            "style": "modern",
            "outdoors": "pool",
        }
    }

    projection = project_result(
        questions=questions,
        answers=answers,
        previous_data=previous_data,
    )

    assert projection.data == {"preferences": {"style": "traditional"}}
    assert "q-outdoors" in projection.inactive_question_ids
    assert "/preferences/style" in projection.changed_paths
    assert "/preferences/outdoors" in projection.changed_paths
    assert "/preferences/outdoors" not in projection.provenance
