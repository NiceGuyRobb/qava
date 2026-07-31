from pathlib import Path

from qava.domain.conditions import evaluate_condition
from qava.infrastructure.contracts.definition_pack import load_definition_pack


def _manifest_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "data"
        / "definitions"
        / "custom-home-intake"
        / "v1"
        / "definition.json"
    )


def test_load_definition_pack_compiles_runtime_questions() -> None:
    pack = load_definition_pack(_manifest_path())

    assert pack.questionnaire_id == "custom-home-intake"
    assert pack.version == 1
    assert len(pack.questions) == 28
    assert pack.questions[0]["mapping"]["target"] == "/project"
    assert pack.questions[0]["presentation"]["name"] == "structured_form"
    assert pack.questions[0]["output_need_ids"] == ["need:project"]


def test_legacy_in_condition_compiles_to_primitive_alternatives() -> None:
    pack = load_definition_pack(_manifest_path())
    site_location = next(
        question for question in pack.questions if question["id"] == "site-location"
    )

    applicability = site_location["applicability"]
    assert evaluate_condition(applicability, {"land-status": "Land owned"}) is True
    assert evaluate_condition(applicability, {"land-status": "Still searching"}) is False


def test_structured_answer_field_can_drive_applicability() -> None:
    pack = load_definition_pack(_manifest_path())
    basement_uses = next(
        question for question in pack.questions if question["id"] == "basement-use"
    )

    applicability = basement_uses["applicability"]
    assert (
        evaluate_condition(
            applicability,
            {"home-structure": {"basement": "Developed basement"}},
        )
        is True
    )
    assert (
        evaluate_condition(
            applicability,
            {"home-structure": {"basement": "No basement"}},
        )
        is False
    )
