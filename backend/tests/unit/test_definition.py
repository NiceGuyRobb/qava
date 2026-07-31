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
