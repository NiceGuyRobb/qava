from __future__ import annotations

import pytest

from qava.domain.answers import validate_answer
from qava.infrastructure.options import (
    ComponentCatalogOptionProvider,
    UnknownOptionProviderError,
    default_option_provider_registry,
)


def test_component_catalog_provider_yields_stable_unique_ids() -> None:
    provider = ComponentCatalogOptionProvider()
    spec = {"provider": "component_catalog", "select": "components"}

    first = provider.resolve(spec)
    second = provider.resolve(spec)

    assert first == second, "choice IDs must be stable across calls"
    ids = [choice["id"] for choice in first]
    assert ids == sorted(ids, key=ids.index)  # order preserved
    assert len(ids) == len(set(ids)), "choice IDs must be unique"
    assert "money_input" in ids


def test_ai_allowed_only_filter_narrows_choices() -> None:
    provider = ComponentCatalogOptionProvider()
    all_ids = {c["id"] for c in provider.resolve({"provider": "component_catalog"})}
    ai_ids = {
        c["id"]
        for c in provider.resolve({"provider": "component_catalog", "ai_allowed_only": True})
    }
    assert ai_ids < all_ids
    assert "boolean" in all_ids and "boolean" not in ai_ids


def test_registry_choices_validate_against_answer_schema() -> None:
    registry = default_option_provider_registry()
    choices = registry.resolve({"provider": "component_catalog", "select": "components"})
    ids = [choice["id"] for choice in choices]

    question = {"answer_schema": {"type": "string", "enum": ids}, "choices": choices}
    assert validate_answer(question, ids[0]) == []
    assert validate_answer(question, "not-a-real-component")


def test_unknown_provider_raises() -> None:
    registry = default_option_provider_registry()
    with pytest.raises(UnknownOptionProviderError):
        registry.resolve({"provider": "does-not-exist"})
