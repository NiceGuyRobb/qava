from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from qava.domain.definition import validate_declared_programme


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    location: str
    message: str


class ContractRegistry:
    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._contracts_dir = repo_root / "data" / "contracts" / "v1"
        self._registry, self._schemas = self._build_schema_registry()

    @property
    def schema_count(self) -> int:
        return len(self._schemas)

    def validate_all(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_schemas())
        issues.extend(self._validate_catalog())
        issues.extend(self._validate_definition_pack())
        issues.extend(self._validate_examples())
        return issues

    def _load_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _build_schema_registry(self) -> tuple[Registry, dict[str, dict[str, Any]]]:
        registry = Registry()
        schemas: dict[str, dict[str, Any]] = {}

        for schema_path in self._contracts_dir.glob("*.schema.json"):
            schema = self._load_json(schema_path)
            if not isinstance(schema, dict):
                continue
            schemas[schema_path.name] = schema

            resource = Resource.from_contents(schema)
            registry = registry.with_resource(schema_path.name, resource)

            schema_id = schema.get("$id")
            if isinstance(schema_id, str) and schema_id:
                registry = registry.with_resource(schema_id, resource)

        return registry, schemas

    def _validate_against(self, schema_name: str, instance: Any) -> list[ValidationIssue]:
        validator = Draft202012Validator(self._schemas[schema_name], registry=self._registry)
        issues: list[ValidationIssue] = []
        for error in validator.iter_errors(instance):
            pointer = "/" + "/".join(str(part) for part in error.absolute_path)
            issues.append(ValidationIssue(location=pointer, message=error.message))
        return issues

    def _validate_schemas(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for schema_name, schema in self._schemas.items():
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:
                issues.append(
                    ValidationIssue(location=f"contracts/{schema_name}", message=str(exc))
                )
        return issues

    def _validate_catalog(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        catalog_path = self._repo_root / "data" / "components" / "catalog.v1.json"
        catalog = self._load_json(catalog_path)

        if not isinstance(catalog, dict):
            return [
                ValidationIssue(location=str(catalog_path), message="Catalog must be an object.")
            ]

        components = catalog.get("components")
        if not isinstance(components, list):
            return [
                ValidationIssue(
                    location=str(catalog_path), message="Catalog components must be a list."
                )
            ]

        names: set[str] = set()
        for index, component in enumerate(components):
            base = f"{catalog_path}:components[{index}]"
            if not isinstance(component, dict):
                issues.append(
                    ValidationIssue(location=base, message="Component entry must be an object.")
                )
                continue

            name = component.get("name")
            if not isinstance(name, str) or not name:
                issues.append(
                    ValidationIssue(location=base, message="Component must include non-empty name.")
                )
            elif name in names:
                issues.append(
                    ValidationIssue(location=base, message=f"Duplicate component name '{name}'.")
                )
            else:
                names.add(name)

            if component.get("renderer_owned_by") != "client":
                issues.append(
                    ValidationIssue(
                        location=base, message="renderer_owned_by must be 'client' in MVP."
                    )
                )

            props_schema = component.get("props_schema")
            if not isinstance(props_schema, dict) or props_schema.get("type") != "object":
                issues.append(
                    ValidationIssue(location=base, message="props_schema must be an object schema.")
                )

        return issues

    def _validate_definition_pack(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        definition_dir = self._repo_root / "data" / "definitions" / "custom-home-intake" / "v1"
        catalog = self._load_json(self._repo_root / "data" / "components" / "catalog.v1.json")
        components = catalog.get("components") if isinstance(catalog, dict) else []
        if not isinstance(components, list):
            return [
                ValidationIssue(
                    location=str(self._repo_root / "data" / "components" / "catalog.v1.json"),
                    message="Catalog components must be a list.",
                )
            ]
        props_schemas = {
            component["name"]: component["props_schema"]
            for component in components
            if isinstance(component, dict)
            and isinstance(component.get("name"), str)
            and isinstance(component.get("props_schema"), dict)
        }

        definition = self._load_json(definition_dir / "definition.json")
        for issue in self._validate_against("definition.schema.json", definition):
            issues.append(
                ValidationIssue(
                    location=f"{definition_dir / 'definition.json'}{issue.location}",
                    message=issue.message,
                )
            )

        question_files = definition.get("question_files") if isinstance(definition, dict) else None
        if not isinstance(question_files, list):
            return issues

        for rel_path in question_files:
            if not isinstance(rel_path, str):
                issues.append(
                    ValidationIssue(
                        location=f"{definition_dir / 'definition.json'}:question_files",
                        message="question_files entries must be strings.",
                    )
                )
                continue

            question_file = definition_dir / rel_path
            payload = self._load_json(question_file)

            questions = payload.get("questions") if isinstance(payload, dict) else None
            if not isinstance(questions, list):
                issues.append(
                    ValidationIssue(
                        location=str(question_file),
                        message="Question file must include a questions array.",
                    )
                )
                continue

            for index, question in enumerate(questions):
                for issue in self._validate_against("question.schema.json", question):
                    issues.append(
                        ValidationIssue(
                            location=f"{question_file}:questions[{index}]{issue.location}",
                            message=issue.message,
                        )
                    )
                if isinstance(question, dict):
                    component_name = question.get("component")
                    props_schema = props_schemas.get(component_name)
                    if isinstance(props_schema, dict):
                        validator = Draft202012Validator(props_schema)
                        for error in validator.iter_errors(question.get("props", {})):
                            pointer = "/" + "/".join(str(part) for part in error.absolute_path)
                            issues.append(
                                ValidationIssue(
                                    location=f"{question_file}:questions[{index}]:props{pointer}",
                                    message=error.message,
                                )
                            )
                    question_id = question.get("id")
                    if isinstance(question_id, str):
                        for issue in validate_declared_programme(question, question_id):
                            issues.append(
                                ValidationIssue(
                                    location=f"{question_file}:questions[{index}]{issue.pointer}",
                                    message=issue.message,
                                )
                            )

        return issues

    def _validate_examples(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        examples_dir = self._repo_root / "data" / "examples" / "custom-home-intake"

        to_validate = {
            "session.snapshot.json": "session.schema.json",
            "insight.json": "insight.schema.json",
            "generated-tradeoff.json": "question.schema.json",
        }

        for file_name, schema_name in to_validate.items():
            payload = self._load_json(examples_dir / file_name)
            for issue in self._validate_against(schema_name, payload):
                issues.append(
                    ValidationIssue(
                        location=f"{examples_dir / file_name}{issue.location}",
                        message=issue.message,
                    )
                )

        return issues
