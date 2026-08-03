"""Runtime option resolution service.

Bridges published questions that declare an ``option_source`` to concrete choices
at request time. Domain evaluation stays pure: it carries the ``option_source``
through on the interaction, and this service resolves it for presentation and for
answer validation.
"""

from __future__ import annotations

import copy
from typing import Any

from qava.infrastructure.options.registry import (
    OptionProviderRegistry,
    default_option_provider_registry,
)
from qava.ports.option_provider import Choice


class OptionResolutionService:
    def __init__(self, registry: OptionProviderRegistry | None = None) -> None:
        self._registry = registry if registry is not None else default_option_provider_registry()

    def resolve_choices(self, question: dict[str, Any]) -> list[Choice] | None:
        """Return runtime choices for *question*, or ``None`` when it has no source."""
        source = question.get("option_source")
        if not isinstance(source, dict):
            return None
        return self._registry.resolve(source)

    def augment_interaction(self, interaction: dict[str, Any] | None) -> dict[str, Any] | None:
        """Inject resolved choices into an outbound interaction (non-mutating)."""
        if interaction is None:
            return None
        choices = self.resolve_choices(interaction)
        if choices is None:
            return interaction
        augmented = copy.deepcopy(interaction)
        _apply_choices(augmented, choices)
        component = augmented.get("component")
        if isinstance(component, dict):
            props = component.setdefault("props", {})
            if isinstance(props, dict):
                props["options"] = [dict(choice) for choice in choices]
        augmented.pop("option_source", None)
        return augmented

    def question_for_validation(self, question: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of *question* with runtime choices applied for validation."""
        choices = self.resolve_choices(question)
        if choices is None:
            return question
        prepared = copy.deepcopy(question)
        _apply_choices(prepared, choices)
        return prepared


def _apply_choices(target: dict[str, Any], choices: list[Choice]) -> None:
    target["choices"] = [dict(choice) for choice in choices]
    choice_ids = [choice["id"] for choice in choices]
    answer_schema = target.get("answer_schema")
    if not isinstance(answer_schema, dict):
        return
    schema_copy = copy.deepcopy(answer_schema)
    if schema_copy.get("type") == "array":
        items = schema_copy.get("items")
        if not isinstance(items, dict):
            items = {"type": "string"}
        items["enum"] = choice_ids
        schema_copy["items"] = items
    else:
        schema_copy["enum"] = choice_ids
    target["answer_schema"] = schema_copy
