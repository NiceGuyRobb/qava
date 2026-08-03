from __future__ import annotations

from typing import Any


def is_component_compatible(
    component_name: str,
    answer_schema: dict[str, Any],
    catalog: dict[str, Any],
) -> bool:
    schema_type = answer_schema.get("type")
    if not isinstance(schema_type, str):
        return False

    shape = _component_shape(component_name, catalog)
    if shape is None:
        return False

    if shape == "scalar":
        return schema_type in {"string", "number", "integer", "boolean"}
    if shape == "asset_reference_array":
        return schema_type == "array"
    if shape == "number":
        return schema_type in {"number", "integer"}
    if shape == "money":
        return schema_type in {"object", "number", "integer"}
    if shape in {"date", "datetime"}:
        return schema_type == "string"
    return shape == schema_type


def infer_component(
    *,
    answer_schema: dict[str, Any],
    catalog: dict[str, Any],
    preferred_component: str,
    fallback_component: str | None,
) -> str:
    if is_component_compatible(preferred_component, answer_schema, catalog):
        return preferred_component

    if fallback_component and is_component_compatible(fallback_component, answer_schema, catalog):
        return fallback_component

    for component in catalog.get("components", []):
        if not isinstance(component, dict):
            continue
        name = component.get("name")
        if isinstance(name, str) and is_component_compatible(name, answer_schema, catalog):
            return name

    raise ValueError("No compatible component found in catalog for answer schema.")


def _component_shape(component_name: str, catalog: dict[str, Any]) -> str | None:
    components = catalog.get("components", [])
    if not isinstance(components, list):
        return None

    for component in components:
        if not isinstance(component, dict):
            continue
        if component.get("name") != component_name:
            continue
        shape = component.get("answer_shape")
        if isinstance(shape, str):
            return shape
        return None

    return None
