from __future__ import annotations

from qava.domain.definition import compile_draft, derive_output_needs, validate_publication


def test_derive_output_needs_marks_required_targets() -> None:
    output_contract = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "budget": {"type": "number"},
        },
        "required": ["name"],
    }

    needs = derive_output_needs(output_contract)

    assert [need["target"] for need in needs] == ["/budget", "/name"]
    required_need = next(need for need in needs if need["target"] == "/name")
    optional_need = next(need for need in needs if need["target"] == "/budget")

    assert required_need["required"] is True
    assert required_need["criticality"] == "blocking"
    assert optional_need["required"] is False
    assert optional_need["criticality"] == "normal"


def test_validate_publication_reports_missing_required_mapping_targets() -> None:
    output_contract = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "budget": {"type": "number"},
        },
        "required": ["name", "budget"],
    }
    questions = [
        {
            "id": "q-name",
            "mapping": {"mode": "direct", "target": "/name"},
        }
    ]

    issues = validate_publication(output_contract=output_contract, questions=questions)

    assert len(issues) == 1
    assert issues[0].code == "missing_required_target"
    assert issues[0].pointer == "/budget"


def test_compile_draft_returns_output_needs_and_validation_issues() -> None:
    output_contract = {
        "type": "object",
        "properties": {
            "rooms": {"type": "integer"},
        },
        "required": ["rooms"],
    }

    draft = compile_draft(
        draft_id="custom-home-intake",
        title="Custom home intake",
        output_contract=output_contract,
        questions=[],
    )

    assert draft["id"] == "custom-home-intake"
    assert len(draft["output_needs"]) == 1
    assert draft["validation_issues"]


def test_validate_publication_reports_field_specific_structured_declaration_issues() -> None:
    question = {
        "id": "home-structure",
        "answer_schema": {
            "type": "object",
            "properties": {
                "needs": {"type": "array", "items": {"type": "string"}},
                "target_area": {"type": "object"},
            },
        },
        "presentation": {
            "name": "structured_form",
            "version": 1,
            "props": {
                "fields": [
                    {"key": "needs", "label": "Needs", "component": "single_select"},
                    {"key": "needs", "label": "Duplicate", "component": "short_text"},
                    {"key": "target_area", "label": "Target area", "component": "measurement"},
                    {"key": "other", "label": "Other", "component": "ranking"},
                ]
            },
        },
    }

    issues = validate_publication(
        output_contract={"type": "object", "properties": {}},
        questions=[question],
    )

    assert {(issue.code, issue.pointer) for issue in issues} == {
        ("duplicate_structured_field_key", "/questions/home-structure/presentation/props/fields/1"),
        ("missing_structured_field_options", "/questions/home-structure/presentation/props/fields/0"),
        ("incompatible_structured_field_shape", "/questions/home-structure/presentation/props/fields/0"),
        ("incompatible_structured_field_shape", "/questions/home-structure/presentation/props/fields/2"),
        ("unsupported_structured_field_component", "/questions/home-structure/presentation/props/fields/3"),
    }


def test_validate_publication_reports_declared_programme_contract_issues() -> None:
    question = {
        "id": "declared-items",
        "answer_schema": {
            "type": "object",
            "properties": {
                "selections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["item_id", "status"],
                        "properties": {
                            "item_id": {"type": "string", "enum": ["item-a", "item-b"]},
                            "status": {"type": "string", "enum": ["required"]},
                            "details": {
                                "type": "object",
                                "properties": {"size": {"type": "string", "enum": ["compact"]}},
                            },
                        },
                    },
                }
            },
        },
        "presentation": {
            "name": "declared_programme",
            "version": 1,
            "props": {
                "groups": [
                    {
                        "id": "group-a",
                        "label": "Group A",
                        "items": [
                            {"value": "item-a", "label": "Item A"},
                            {"value": "item-a", "label": "Duplicate"},
                        ],
                    },
                    {"id": "group-a", "label": "Duplicate group", "items": []},
                ],
                "statuses": [{"value": "required", "label": "Required"}],
                "details": [
                    {"key": "size", "label": "Size", "component": "single_select"},
                    {"key": "size", "label": "Duplicate", "component": "unsupported"},
                ],
            },
        },
    }

    issues = validate_publication(
        output_contract={"type": "object", "properties": {}},
        questions=[question],
    )

    assert {issue.code for issue in issues} == {
        "duplicate_programme_group_id",
        "empty_programme_group",
        "duplicate_programme_item_value",
        "missing_programme_detail_options",
        "duplicate_programme_detail_key",
        "unsupported_programme_detail_component",
        "incompatible_programme_answer_schema",
    }
