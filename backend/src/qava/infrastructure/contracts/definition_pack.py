from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True, slots=True)
class CompiledDefinitionPack:
    questionnaire_id: str
    version: int
    title: str
    description: str | None
    output_contract: dict[str, Any]
    questions: list[dict[str, Any]]


def load_definition_pack(manifest_path: Path) -> CompiledDefinitionPack:
    manifest = _load_object(manifest_path)
    base_dir = manifest_path.parent
    output_contract = _load_object(base_dir / _required_string(manifest, "contract"))
    question_payloads = [
        _load_object(base_dir / relative_path)
        for relative_path in _required_string_list(manifest, "question_files")
    ]

    source_questions = [
        question
        for payload in question_payloads
        for question in _required_object_list(payload, "questions")
    ]
    question_ids_by_path = {
        _required_string(question, "path"): _required_string(question, "id")
        for question in source_questions
    }
    questions = [
        _compile_question(question, question_ids_by_path, order)
        for order, question in enumerate(source_questions, start=1)
    ]

    return CompiledDefinitionPack(
        questionnaire_id=_required_string(manifest, "id"),
        version=_required_int(manifest, "version"),
        title=_required_string(manifest, "title"),
        description=_optional_string(manifest, "description"),
        output_contract=output_contract,
        questions=questions,
    )


def _compile_question(
    source: dict[str, Any],
    question_ids_by_path: dict[str, str],
    order: int,
) -> dict[str, Any]:
    path = _required_string(source, "path")
    component = _required_string(source, "component")
    raw_props = source.get("props")
    props = cast(dict[str, Any], raw_props) if isinstance(raw_props, dict) else {}
    choices = _compile_choices(props)
    question: dict[str, Any] = {
        "id": _required_string(source, "id"),
        "topic_id": _required_string(source, "topic_id"),
        "prompt": _required_string(source, "prompt"),
        "help_text": _optional_string(source, "help_text"),
        "output_need_ids": [f"need:{path.split('.', 1)[0]}"],
        "answer_schema": _answer_schema(source, component, choices),
        "mapping": {"mode": "direct", "target": _json_pointer(path)},
        "presentation": {"name": component, "version": 1, "props": props},
        "required": source.get("required") is True,
        "order": order,
    }
    if choices:
        question["choices"] = choices

    option_source = source.get("option_source")
    if isinstance(option_source, dict):
        question["option_source"] = option_source

    condition = source.get("when")
    if isinstance(condition, dict):
        question["applicability"] = _compile_condition(condition, question_ids_by_path)
    return question


def _compile_condition(
    source: dict[str, Any], question_ids_by_path: dict[str, str]
) -> dict[str, Any]:
    source_path = _required_string(source, "path")
    owning_path = max(
        (
            question_path
            for question_path in question_ids_by_path
            if source_path == question_path or source_path.startswith(f"{question_path}.")
        ),
        key=len,
        default=None,
    )
    if owning_path is None:
        raise ValueError(f"Condition source path {source_path!r} has no question.")
    source_question_id = question_ids_by_path[owning_path]
    source_value_path = source_path.removeprefix(owning_path).removeprefix(".")

    def primitive(operator: str, value: Any = None, *, has_value: bool = True) -> dict[str, Any]:
        compiled: dict[str, Any] = {
            "source_question_id": source_question_id,
            "operator": operator,
        }
        if source_value_path:
            compiled["source_value_path"] = source_value_path
        if has_value:
            compiled["value"] = value
        return compiled

    operator = _required_string(source, "operator")
    if operator == "in":
        values = source.get("value")
        if not isinstance(values, list) or not values:
            raise ValueError("The legacy 'in' condition requires a non-empty value list.")
        return {"any": [primitive("equals", value) for value in values]}

    return primitive(operator, source.get("value"), has_value="value" in source)


def _compile_choices(props: dict[str, Any]) -> list[dict[str, str]]:
    options = props.get("options")
    if not isinstance(options, list):
        return []

    choices: list[dict[str, str]] = []
    for option in options:
        if isinstance(option, str):
            choices.append({"id": option, "label": option})
        elif isinstance(option, dict):
            value = option.get("value")
            label = option.get("label")
            if isinstance(value, str) and isinstance(label, str):
                choices.append({"id": value, "label": label})
    return choices


def _answer_schema(
    source: dict[str, Any], component: str, choices: list[dict[str, str]]
) -> dict[str, Any]:
    declared = source.get("answer_schema")
    if isinstance(declared, dict):
        return declared

    choice_ids = [choice["id"] for choice in choices]
    if component in {"multi_select", "ranking"}:
        items: dict[str, Any] = {"type": "string"}
        if choice_ids:
            items["enum"] = choice_ids
        return {"type": "array", "items": items, "uniqueItems": True}
    if component in {"repeatable_group", "file_upload"}:
        return {"type": "array"}
    if component == "number":
        return {"type": "number"}
    if component == "money_input":
        return {"type": "number"}
    if component == "date_picker":
        return {"type": "string", "format": "date"}
    if component == "datetime_picker":
        return {"type": "string", "format": "date-time"}
    if component in {"structured_form", "address", "measurement", "room_programme"}:
        return {"type": "object"}
    if component in {"boolean", "confirmation"}:
        return {"type": "boolean"}
    if choice_ids:
        return {"type": "string", "enum": choice_ids}
    return {"type": "string"}


def _json_pointer(path: str) -> str:
    return "/" + "/".join(part.replace("~", "~0").replace("/", "~1") for part in path.split("."))


def _load_object(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return loaded


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key!r} must be a non-empty string.")
    return value


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key!r} must be a string when present.")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key!r} must be an integer.")
    return value


def _required_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key!r} must be a list of strings.")
    return value


def _required_object_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{key!r} must be a list of objects.")
    return value
