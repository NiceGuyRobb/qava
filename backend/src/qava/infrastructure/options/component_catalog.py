"""Option provider backed by the component catalog.

This is the first concrete provider and the lowest-coupling one: it serves the
catalogue of UI components as selectable options. Authoring flows (US5) use it so
an author picks a component from the live catalog instead of a hand-maintained
list, and it demonstrates the runtime option-source seam end to end.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from qava.ports.option_provider import Choice

_REPO_ROOT = Path(__file__).resolve().parents[5]
_CATALOG_PATH = _REPO_ROOT / "data" / "components" / "catalog.v1.json"


@lru_cache(maxsize=1)
def load_component_catalog() -> dict[str, Any]:
    """Load the bundled component catalog once."""
    loaded = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("Component catalog must be a JSON object.")
    return loaded


class ComponentCatalogOptionProvider:
    """Resolves options from the component catalog."""

    name = "component_catalog"

    def __init__(self, catalog: Mapping[str, Any] | None = None) -> None:
        self._catalog = catalog if catalog is not None else load_component_catalog()

    def resolve(self, spec: Mapping[str, Any]) -> list[Choice]:
        select = spec.get("select", "components")
        if select != "components":
            raise ValueError(f"Unsupported component_catalog select {select!r}.")

        ai_allowed_only = spec.get("ai_allowed_only") is True
        components = self._catalog.get("components")
        if not isinstance(components, list):
            return []

        choices: list[Choice] = []
        for component in components:
            if not isinstance(component, dict):
                continue
            component_name = component.get("name")
            if not isinstance(component_name, str) or not component_name:
                continue
            if ai_allowed_only and component.get("ai_allowed") is not True:
                continue
            choices.append({"id": component_name, "label": component_name})
        return choices
