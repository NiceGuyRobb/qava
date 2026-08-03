from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DefinitionIssue:
    code: str
    message: str
    pointer: str


def derive_output_needs(output_contract: dict[str, Any]) -> list[dict[str, Any]]:
    root_type = output_contract.get("type")
    if root_type != "object":
        return []

    properties = output_contract.get("properties", {})
    required = {entry for entry in output_contract.get("required", []) if isinstance(entry, str)}

    needs: list[dict[str, Any]] = []
    for key in sorted(properties.keys()):
        schema = properties.get(key)
        if not isinstance(schema, dict):
            continue

        pointer = f"/{key}"
        is_required = key in required
        needs.append(
            {
                "id": f"need:{key}",
                "target": pointer,
                "value_schema": schema,
                "required": is_required,
                "criticality": "blocking" if is_required else "normal",
                "weight": 1.0,
            }
        )

    return needs


def validate_publication(
    *,
    output_contract: dict[str, Any],
    questions: list[dict[str, Any]],
) -> list[DefinitionIssue]:
    issues: list[DefinitionIssue] = []
    output_needs = derive_output_needs(output_contract)

    declared_targets = _declared_mapping_targets(questions)

    for need in output_needs:
        target = need["target"]
        is_served = any(
            declared == target or declared.startswith(f"{target}/") for declared in declared_targets
        )
        if need["required"] and not is_served:
            issues.append(
                DefinitionIssue(
                    code="missing_required_target",
                    message=f"No question mapping target serves required output need at {target}.",
                    pointer=target,
                )
            )

    seen_question_ids: set[str] = set()
    for question in questions:
        question_id = question.get("id")
        if not isinstance(question_id, str):
            continue
        if question_id in seen_question_ids:
            issues.append(
                DefinitionIssue(
                    code="duplicate_question_id",
                    message=f"Question id {question_id!r} must be unique.",
                    pointer=f"/questions/{question_id}",
                )
            )
        seen_question_ids.add(question_id)
        issues.extend(_validate_structured_fields(question, question_id))
        issues.extend(_validate_declared_programme(question, question_id))

    return issues


def compile_draft(
    *,
    draft_id: str,
    title: str,
    output_contract: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    output_needs = derive_output_needs(output_contract)
    issues = validate_publication(output_contract=output_contract, questions=questions)

    return {
        "id": draft_id,
        "title": title,
        "output_contract": output_contract,
        "output_needs": output_needs,
        "questions": questions,
        "validation_issues": [
            {"code": issue.code, "message": issue.message, "pointer": issue.pointer}
            for issue in issues
        ],
        "compiled_at": datetime.now(UTC).isoformat(),
    }


def _declared_mapping_targets(questions: list[dict[str, Any]]) -> set[str]:
    targets: set[str] = set()
    for question in questions:
        mapping = question.get("mapping")
        if not isinstance(mapping, dict):
            continue
        target = mapping.get("target")
        if isinstance(target, str):
            targets.add(target)
    return targets


def _validate_structured_fields(question: dict[str, Any], question_id: str) -> list[DefinitionIssue]:
    presentation = question.get("presentation")
    if not isinstance(presentation, dict):
        return []

    presentation_name = presentation.get("name")
    if presentation_name not in {"structured_form", "repeatable_group"}:
        return []

    props = presentation.get("props")
    if not isinstance(props, dict) or "fields" not in props:
        return []

    fields = props["fields"]
    fields_pointer = f"/questions/{question_id}/presentation/props/fields"
    if not isinstance(fields, list):
        return [
            DefinitionIssue(
                code="invalid_structured_fields",
                message="Structured component fields must be a list.",
                pointer=fields_pointer,
            )
        ]

    answer_schema = question.get("answer_schema")
    schema = answer_schema if isinstance(answer_schema, dict) else {}
    if presentation_name == "repeatable_group":
        item_schema = schema.get("items")
        schema = item_schema if isinstance(item_schema, dict) else {}
    properties = schema.get("properties")
    property_schemas = properties if isinstance(properties, dict) else {}

    issues: list[DefinitionIssue] = []
    seen_keys: set[str] = set()
    supported_components = {
        "short_text",
        "long_text",
        "number",
        "boolean",
        "single_select",
        "multi_select",
        "measurement",
    }
    for index, field in enumerate(fields):
        pointer = f"{fields_pointer}/{index}"
        if not isinstance(field, dict):
            issues.append(
                DefinitionIssue(
                    code="invalid_structured_field",
                    message="Structured field declarations must be objects.",
                    pointer=pointer,
                )
            )
            continue

        key = field.get("key")
        label = field.get("label")
        component = field.get("component")
        if not isinstance(key, str) or not key or not isinstance(label, str) or not label:
            issues.append(
                DefinitionIssue(
                    code="invalid_structured_field",
                    message="Structured fields require non-empty key and label values.",
                    pointer=pointer,
                )
            )
            continue
        if key in seen_keys:
            issues.append(
                DefinitionIssue(
                    code="duplicate_structured_field_key",
                    message=f"Structured field key {key!r} must be unique.",
                    pointer=pointer,
                )
            )
            continue
        seen_keys.add(key)

        if component not in supported_components:
            issues.append(
                DefinitionIssue(
                    code="unsupported_structured_field_component",
                    message=f"Structured field component {component!r} is not supported.",
                    pointer=pointer,
                )
            )
            continue

        if component in {"single_select", "multi_select"} and not _has_choices(field.get("options")):
            issues.append(
                DefinitionIssue(
                    code="missing_structured_field_options",
                    message=f"Structured {component} fields require at least one option.",
                    pointer=pointer,
                )
            )

        field_schema = property_schemas.get(key)
        if isinstance(field_schema, dict) and not _is_field_schema_compatible(component, field_schema):
            issues.append(
                DefinitionIssue(
                    code="incompatible_structured_field_shape",
                    message=f"Structured field {key!r} is incompatible with component {component!r}.",
                    pointer=pointer,
                )
            )

    return issues


def validate_declared_programme(question: dict[str, Any], question_id: str) -> list[DefinitionIssue]:
    return _validate_declared_programme(question, question_id)


def _validate_declared_programme(question: dict[str, Any], question_id: str) -> list[DefinitionIssue]:
    presentation = question.get("presentation")
    if isinstance(presentation, dict):
        name = presentation.get("name")
        props = presentation.get("props")
        base_pointer = f"/questions/{question_id}/presentation/props"
    else:
        name = question.get("component")
        props = question.get("props")
        base_pointer = f"/questions/{question_id}/props"
    if name != "declared_programme":
        return []
    if not isinstance(props, dict):
        return [_programme_issue("invalid_programme_declaration", "Programme props must be an object.", base_pointer)]

    issues: list[DefinitionIssue] = []
    groups = props.get("groups")
    statuses = props.get("statuses")
    details = props.get("details", [])
    item_values: list[str] = []
    status_values: list[str] = []
    detail_values: list[tuple[str, str, object]] = []

    if not isinstance(groups, list) or not groups:
        issues.append(_programme_issue("missing_programme_groups", "Programme groups must be a non-empty list.", f"{base_pointer}/groups"))
    else:
        group_ids: set[str] = set()
        item_ids: set[str] = set()
        for index, group in enumerate(groups):
            pointer = f"{base_pointer}/groups/{index}"
            if not isinstance(group, dict):
                issues.append(_programme_issue("invalid_programme_group", "Programme groups must be objects.", pointer))
                continue
            group_id = group.get("id")
            if not isinstance(group_id, str) or not group_id:
                issues.append(_programme_issue("invalid_programme_group", "Programme groups require a non-empty id.", pointer))
            elif group_id in group_ids:
                issues.append(_programme_issue("duplicate_programme_group_id", f"Programme group id {group_id!r} must be unique.", pointer))
            else:
                group_ids.add(group_id)
            if not isinstance(group.get("label"), str) or not group["label"]:
                issues.append(_programme_issue("invalid_programme_group", "Programme groups require a non-empty label.", pointer))
            items = group.get("items")
            if not isinstance(items, list) or not items:
                issues.append(_programme_issue("empty_programme_group", "Programme groups require at least one item.", pointer))
                continue
            for item_index, item in enumerate(items):
                item_pointer = f"{pointer}/items/{item_index}"
                value = _programme_value(item, "value")
                label = _programme_value(item, "label")
                if value is None or label is None:
                    issues.append(_programme_issue("invalid_programme_item", "Programme items require non-empty value and label fields.", item_pointer))
                    continue
                if value in item_ids:
                    issues.append(_programme_issue("duplicate_programme_item_value", f"Programme item value {value!r} must be unique.", item_pointer))
                else:
                    item_ids.add(value)
                item_values.append(value)

    if not isinstance(statuses, list) or not statuses:
        issues.append(_programme_issue("missing_programme_statuses", "Programme statuses must be a non-empty list.", f"{base_pointer}/statuses"))
    else:
        seen_statuses: set[str] = set()
        for index, status in enumerate(statuses):
            pointer = f"{base_pointer}/statuses/{index}"
            value = _programme_value(status, "value")
            if value is None or _programme_value(status, "label") is None:
                issues.append(_programme_issue("invalid_programme_status", "Programme statuses require non-empty value and label fields.", pointer))
                continue
            if value in seen_statuses:
                issues.append(_programme_issue("duplicate_programme_status_value", f"Programme status value {value!r} must be unique.", pointer))
            else:
                seen_statuses.add(value)
            status_values.append(value)

    if not isinstance(details, list):
        issues.append(_programme_issue("invalid_programme_details", "Programme details must be a list.", f"{base_pointer}/details"))
    else:
        seen_details: set[str] = set()
        for index, detail in enumerate(details):
            pointer = f"{base_pointer}/details/{index}"
            key = _programme_value(detail, "key")
            component = detail.get("component") if isinstance(detail, dict) else None
            if key is None or _programme_value(detail, "label") is None:
                issues.append(_programme_issue("invalid_programme_detail", "Programme details require non-empty key and label fields.", pointer))
                continue
            if key in seen_details:
                issues.append(_programme_issue("duplicate_programme_detail_key", f"Programme detail key {key!r} must be unique.", pointer))
            else:
                seen_details.add(key)
            if component not in {"single_select", "short_text", "long_text", "number", "boolean"}:
                issues.append(_programme_issue("unsupported_programme_detail_component", f"Programme detail component {component!r} is not supported.", pointer))
                continue
            if component == "single_select":
                options = detail.get("options") if isinstance(detail, dict) else None
                if not isinstance(options, list) or not options:
                    issues.append(_programme_issue("missing_programme_detail_options", "Programme single_select details require options.", pointer))
                    continue
                option_values = [_programme_value(option, "value") for option in options]
                if any(value is None for value in option_values) or len(set(option_values)) != len(option_values):
                    issues.append(_programme_issue("invalid_programme_detail_options", "Programme detail options require unique non-empty values and labels.", pointer))
                detail_values.append((key, component, [value for value in option_values if value is not None]))
            else:
                detail_values.append((key, component, None))

    if not _programme_schema_matches(question.get("answer_schema"), item_values, status_values, detail_values):
        issues.append(_programme_issue("incompatible_programme_answer_schema", "Programme answer schema must declare compatible selections, stable enums, and details.", f"/questions/{question_id}/answer_schema"))
    return issues


def _programme_issue(code: str, message: str, pointer: str) -> DefinitionIssue:
    return DefinitionIssue(code=code, message=message, pointer=pointer)


def _programme_value(value: object, key: str) -> str | None:
    candidate = value.get(key) if isinstance(value, dict) else None
    return candidate if isinstance(candidate, str) and candidate else None


def _programme_schema_matches(
    answer_schema: object,
    item_values: list[str],
    status_values: list[str],
    details: list[tuple[str, str, object]],
) -> bool:
    if not isinstance(answer_schema, dict) or answer_schema.get("type") != "object":
        return False
    properties = answer_schema.get("properties")
    selections = properties.get("selections") if isinstance(properties, dict) else None
    if not isinstance(selections, dict) or selections.get("type") != "array":
        return False
    item_schema = selections.get("items")
    item_properties = item_schema.get("properties") if isinstance(item_schema, dict) else None
    required = item_schema.get("required") if isinstance(item_schema, dict) else None
    if not isinstance(item_properties, dict) or not isinstance(required, list) or {"item_id", "status"} - set(required):
        return False
    if not _schema_enum_matches(item_properties.get("item_id"), item_values) or not _schema_enum_matches(item_properties.get("status"), status_values):
        return False
    if not details:
        return "details" not in item_properties
    detail_schema = item_properties.get("details")
    detail_properties = detail_schema.get("properties") if isinstance(detail_schema, dict) else None
    if not isinstance(detail_schema, dict) or detail_schema.get("type") != "object" or not isinstance(detail_properties, dict):
        return False
    if set(detail_properties) != {key for key, _, _ in details}:
        return False
    return all(_detail_schema_matches(detail_properties[key], component, options) for key, component, options in details)


def _schema_enum_matches(schema: object, values: list[str]) -> bool:
    return isinstance(schema, dict) and schema.get("type") == "string" and schema.get("enum") == values


def _detail_schema_matches(schema: object, component: str, options: object) -> bool:
    if not isinstance(schema, dict):
        return False
    if component == "single_select":
        return _schema_enum_matches(schema, options if isinstance(options, list) else [])
    if component == "number":
        return schema.get("type") in {"number", "integer"}
    return schema.get("type") == ("boolean" if component == "boolean" else "string")


def _has_choices(value: object) -> bool:
    return isinstance(value, list) and bool(value)


def _is_field_schema_compatible(component: object, schema: dict[str, Any]) -> bool:
    schema_type = schema.get("type")
    if component in {"short_text", "long_text"}:
        return schema_type == "string"
    if component == "number":
        return schema_type in {"number", "integer"}
    if component == "boolean":
        return schema_type == "boolean"
    if component == "single_select":
        return schema_type in {"string", "number", "integer", "boolean"}
    if component == "multi_select":
        return schema_type == "array"
    if component != "measurement" or schema_type != "object":
        return False

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return False
    value_schema = properties.get("value")
    unit_schema = properties.get("unit")
    return (
        isinstance(value_schema, dict)
        and value_schema.get("type") in {"number", "integer"}
        and isinstance(unit_schema, dict)
        and unit_schema.get("type") == "string"
    )
