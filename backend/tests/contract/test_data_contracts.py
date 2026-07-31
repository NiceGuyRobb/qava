from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPO_ROOT / "data" / "contracts" / "v1"
DEFINITION_DIR = REPO_ROOT / "data" / "definitions" / "custom-home-intake" / "v1"
EXAMPLES_DIR = REPO_ROOT / "data" / "examples" / "custom-home-intake"
CATALOG_PATH = REPO_ROOT / "data" / "components" / "catalog.v1.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_schema_registry() -> tuple[Registry, dict[str, dict[str, Any]]]:
    registry = Registry()
    schemas: dict[str, dict[str, Any]] = {}

    for schema_path in CONTRACTS_DIR.glob("*.schema.json"):
        schema = _load_json(schema_path)
        assert isinstance(schema, dict)
        schemas[schema_path.name] = schema

        resource = Resource.from_contents(schema)
        registry = registry.with_resource(schema_path.name, resource)

        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            registry = registry.with_resource(schema_id, resource)

    return registry, schemas


def _validate_against(
    schema_name: str,
    instance: Any,
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> None:
    validator = Draft202012Validator(schemas[schema_name], registry=registry)
    validator.validate(instance)


def test_contract_schemas_are_loadable_and_self_valid() -> None:
    registry, schemas = _build_schema_registry()

    assert registry is not None
    assert len(schemas) >= 5

    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)


def test_component_catalog_entries_have_required_structure() -> None:
    payload = _load_json(CATALOG_PATH)

    assert isinstance(payload, dict)
    assert payload.get("schema_version") == 1

    components = payload.get("components")
    assert isinstance(components, list)
    assert components

    names: set[str] = set()
    for entry in components:
        assert isinstance(entry, dict)
        assert isinstance(entry.get("name"), str)
        assert entry["name"] not in names
        names.add(entry["name"])

        assert entry.get("renderer_owned_by") == "client"
        assert isinstance(entry.get("answer_shape"), str)

        props_schema = entry.get("props_schema")
        assert isinstance(props_schema, dict)
        assert props_schema.get("type") == "object"


def test_definition_pack_files_match_contracts() -> None:
    registry, schemas = _build_schema_registry()

    definition = _load_json(DEFINITION_DIR / "definition.json")
    _validate_against("definition.schema.json", definition, registry, schemas)

    topics_payload = _load_json(DEFINITION_DIR / "topics.json")
    assert isinstance(topics_payload, dict)
    assert topics_payload.get("schema_version") == 1

    topics = topics_payload.get("topics")
    assert isinstance(topics, list)
    assert topics

    topic_ids: set[str] = set()
    for topic in topics:
        assert isinstance(topic, dict)
        topic_id = topic.get("id")
        assert isinstance(topic_id, str)
        assert topic_id not in topic_ids
        topic_ids.add(topic_id)

    question_files = definition.get("question_files")
    assert isinstance(question_files, list)
    assert question_files

    question_ids: set[str] = set()
    for rel_path in question_files:
        assert isinstance(rel_path, str)
        question_doc = _load_json(DEFINITION_DIR / rel_path)

        assert isinstance(question_doc, dict)
        assert question_doc.get("schema_version") == 1

        questions = question_doc.get("questions")
        assert isinstance(questions, list)
        assert questions

        file_topic_id = question_doc.get("topic_id")
        assert isinstance(file_topic_id, str)
        assert file_topic_id in topic_ids

        for question in questions:
            _validate_against("question.schema.json", question, registry, schemas)

            question_id = question.get("id")
            assert isinstance(question_id, str)
            assert question_id not in question_ids
            question_ids.add(question_id)

            assert question.get("topic_id") == file_topic_id


def test_example_fixtures_match_core_contract_expectations() -> None:
    registry, schemas = _build_schema_registry()

    session_snapshot = _load_json(EXAMPLES_DIR / "session.snapshot.json")
    _validate_against("session.schema.json", session_snapshot, registry, schemas)

    insight = _load_json(EXAMPLES_DIR / "insight.json")
    _validate_against("insight.schema.json", insight, registry, schemas)

    generated_tradeoff = _load_json(EXAMPLES_DIR / "generated-tradeoff.json")
    _validate_against("question.schema.json", generated_tradeoff, registry, schemas)

    clarification_request = _load_json(EXAMPLES_DIR / "clarification-request.json")
    assert isinstance(clarification_request, dict)
    for required_key in ["question", "answer", "constraints", "allowed_components"]:
        assert required_key in clarification_request

    clarification_response = _load_json(EXAMPLES_DIR / "clarification-response.json")
    assert isinstance(clarification_response, dict)
    assert "question" in clarification_response

    result = _load_json(EXAMPLES_DIR / "result.json")
    assert isinstance(result, dict)
    for required_key in ["session_id", "questionnaire", "revision", "data", "health"]:
        assert required_key in result
