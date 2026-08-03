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


def test_home_structure_declares_nested_measurement_and_multi_select_shapes() -> None:
    pack = load_definition_pack(_manifest_path())
    home_structure = next(question for question in pack.questions if question["id"] == "home-structure")

    assert home_structure["mapping"]["target"] == "/structure"
    assert home_structure["answer_schema"] == {
        "type": "object",
        "properties": {
            "target_area": {
                "type": "object",
                "required": ["value", "unit"],
                "properties": {
                    "value": {"type": "number", "minimum": 1},
                    "unit": {"type": "string", "enum": ["sq_ft", "sq_m"]},
                },
            },
            "ceiling_preferences": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "Standard throughout",
                        "Raised main-floor ceilings",
                        "Vaulted living area",
                        "Double-height space",
                        "Raised basement ceilings",
                    ],
                },
                "uniqueItems": True,
            },
        },
    }


def test_ranking_items_compile_to_runtime_choices_and_schema_enum() -> None:
    pack = load_definition_pack(_manifest_path())
    space_priorities = next(question for question in pack.questions if question["id"] == "space-priorities")

    assert space_priorities["choices"] == [
        {"id": "Kitchen", "label": "Kitchen"},
        {"id": "Primary suite", "label": "Primary suite"},
        {"id": "Main living area", "label": "Main living area"},
        {"id": "Outdoor living", "label": "Outdoor living"},
        {"id": "Home office", "label": "Home office"},
        {"id": "Home gym or wellness", "label": "Home gym or wellness"},
        {"id": "Guest accommodation", "label": "Guest accommodation"},
        {"id": "Mudroom and entry", "label": "Mudroom and entry"},
        {"id": "Basement recreation", "label": "Basement recreation"},
        {"id": "Garage", "label": "Garage"},
        {"id": "Wine storage", "label": "Wine storage"},
        {"id": "Sauna or cold plunge", "label": "Sauna or cold plunge"},
    ]
    assert space_priorities["answer_schema"] == {
        "type": "array",
        "items": {
            "type": "string",
            "enum": [choice["id"] for choice in space_priorities["choices"]],
        },
        "uniqueItems": True,
    }


def test_visual_cards_compile_to_runtime_choices_and_schema_enum() -> None:
    pack = load_definition_pack(_manifest_path())
    overall_style = next(question for question in pack.questions if question["id"] == "overall-style")

    assert overall_style["choices"] == [
        {"id": "contemporary", "label": "Contemporary"},
        {"id": "farmhouse", "label": "Farmhouse"},
        {"id": "midcentury", "label": "Mid-century"},
        {"id": "japandi", "label": "Japandi"},
        {"id": "mediterranean", "label": "Mediterranean"},
    ]
    assert overall_style["answer_schema"] == {
        "type": "string",
        "enum": [choice["id"] for choice in overall_style["choices"]],
    }


def test_declared_programme_preserves_typed_contract_and_mapping() -> None:
    pack = load_definition_pack(_manifest_path())
    room_programme = next(question for question in pack.questions if question["id"] == "room-programme")

    assert room_programme["mapping"]["target"] == "/rooms/programme"
    assert room_programme["presentation"] == {
        "name": "declared_programme",
        "version": 1,
        "props": {
            "statuses": [
                {"value": "required", "label": "Required"},
                {"value": "possible", "label": "Possible"},
                {"value": "not_needed", "label": "Not needed"},
            ],
            "groups": room_programme["presentation"]["props"]["groups"],
            "details": room_programme["presentation"]["props"]["details"],
        },
    }
    assert room_programme["presentation"]["props"]["groups"][0] == {
        "id": "entry",
        "label": "Entry & Main Floor",
        "items": [
            {"value": "front_foyer", "label": "Front foyer"},
            {"value": "mudroom", "label": "Mudroom"},
            {"value": "main_floor_office", "label": "Main-floor office or den"},
            {"value": "powder_room", "label": "Powder room"},
        ],
    }
    assert room_programme["answer_schema"] == {
        "type": "object",
        "additionalProperties": False,
        "required": ["selections"],
        "properties": {
            "selections": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["item_id", "status"],
                    "properties": room_programme["answer_schema"]["properties"]["selections"][
                        "items"
                    ]["properties"],
                },
            }
        },
    }
    selection_properties = room_programme["answer_schema"]["properties"]["selections"][
        "items"
    ]["properties"]
    assert selection_properties["item_id"]["enum"] == [
        item["value"]
        for group in room_programme["presentation"]["props"]["groups"]
        for item in group["items"]
    ]
    assert selection_properties["status"]["enum"] == ["required", "possible", "not_needed"]
    assert selection_properties["details"]["properties"]["size"]["enum"] == [
        "compact",
        "standard",
        "generous",
        "not_sure",
    ]
