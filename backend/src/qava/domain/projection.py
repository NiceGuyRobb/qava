from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qava.domain.conditions import evaluate_condition

# Structural limits mirror the foundation constraints in qava.config. They are
# duplicated here as constants to keep the projection domain pure.
MAX_COMPOSE_DEPTH = 3
MAX_COLLECTION_ITEMS = 100


@dataclass(frozen=True)
class ProjectionResult:
    data: dict[str, Any]
    provenance: dict[str, dict[str, list[str]]]
    changed_paths: list[str]
    inactive_question_ids: list[str]


def project_result(
    *,
    questions: list[dict[str, Any]],
    answers: dict[str, Any],
    previous_data: dict[str, Any] | None = None,
) -> ProjectionResult:
    data: dict[str, Any] = {}
    provenance: dict[str, dict[str, list[str]]] = {}
    inactive_question_ids: list[str] = []

    active_answers: dict[str, Any] = {}
    compose_mappings: list[tuple[dict[str, Any], str, dict[str, Any]]] = []

    for question in questions:
        question_id = question.get("id")
        if not isinstance(question_id, str):
            continue
        mapping = question.get("mapping")
        if not isinstance(mapping, dict):
            continue

        mode = mapping.get("mode")
        target = mapping.get("target")
        if not isinstance(mode, str) or not isinstance(target, str):
            continue

        if not evaluate_condition(question.get("applicability"), active_answers):
            if question_id in answers:
                inactive_question_ids.append(question_id)
            continue

        if mode == "direct":
            if question_id not in answers:
                continue
            answer_value = answers[question_id]
            active_answers[question_id] = answer_value
            _set_pointer(data, target, answer_value)
            provenance[target] = {"question_ids": [question_id]}
            continue

        if mode == "compose":
            compose_mappings.append((question, target, mapping))

    for question, target, mapping in compose_mappings:
        if not evaluate_condition(question.get("applicability"), active_answers):
            continue
        composed_value, source_ids = _compose_value(mapping, active_answers)
        if composed_value is None:
            continue
        _set_pointer(data, target, composed_value)
        provenance[target] = {"question_ids": source_ids}

    changed_paths = _collect_changed_paths(previous_data or {}, data)

    return ProjectionResult(
        data=data,
        provenance=provenance,
        changed_paths=changed_paths,
        inactive_question_ids=inactive_question_ids,
    )


def _compose_value(
    mapping: dict[str, Any],
    active_answers: dict[str, Any],
    *,
    depth: int = 0,
) -> tuple[Any | None, list[str]]:
    if depth > MAX_COMPOSE_DEPTH:
        return None, []

    sources = mapping.get("sources")
    shape = mapping.get("shape")

    if shape == "object" and isinstance(sources, dict):
        composed: dict[str, Any] = {}
        source_ids: list[str] = []
        for key, source_spec in sources.items():
            if not isinstance(key, str):
                continue
            value, sub_ids = _resolve_source(source_spec, active_answers, depth)
            if value is None and not sub_ids:
                return None, []
            composed[key] = value
            source_ids.extend(sub_ids)
        return composed, source_ids

    if shape == "array" and isinstance(sources, list):
        values: list[Any] = []
        source_ids = []
        for source_spec in sources[:MAX_COLLECTION_ITEMS]:
            value, sub_ids = _resolve_source(source_spec, active_answers, depth)
            if value is None and not sub_ids:
                return None, []
            values.append(value)
            source_ids.extend(sub_ids)
        return values, source_ids

    return None, []


def _resolve_source(
    source_spec: Any,
    active_answers: dict[str, Any],
    depth: int,
) -> tuple[Any | None, list[str]]:
    """Resolve one compose source: a question id or a nested compose mapping."""
    if isinstance(source_spec, str):
        if source_spec not in active_answers:
            return None, []
        return active_answers[source_spec], [source_spec]
    if isinstance(source_spec, dict) and "shape" in source_spec:
        return _compose_value(source_spec, active_answers, depth=depth + 1)
    return None, []


def _set_pointer(root: dict[str, Any], pointer: str, value: Any) -> None:
    parts = [part for part in pointer.split("/") if part]
    if not parts:
        return

    current: dict[str, Any] = root
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested

    current[parts[-1]] = value


def _collect_changed_paths(previous: Any, current: Any, pointer: str = "") -> list[str]:
    if type(previous) is not type(current):
        return [pointer or "/"]

    if isinstance(previous, dict) and isinstance(current, dict):
        changed: list[str] = []
        all_keys = set(previous) | set(current)
        for key in sorted(all_keys):
            next_pointer = f"{pointer}/{key}" if pointer else f"/{key}"
            if key not in previous or key not in current:
                changed.append(next_pointer)
                continue
            changed.extend(_collect_changed_paths(previous[key], current[key], next_pointer))
        return changed

    if isinstance(previous, list) and isinstance(current, list):
        if previous == current:
            return []
        return [pointer or "/"]

    if previous != current:
        return [pointer or "/"]

    return []
