from __future__ import annotations

from qava.domain.components import is_component_compatible
from qava.infrastructure.options.component_catalog import load_component_catalog


def test_money_input_compatible_with_object_and_number() -> None:
    catalog = load_component_catalog()
    assert is_component_compatible("money_input", {"type": "object"}, catalog)
    assert is_component_compatible("money_input", {"type": "number"}, catalog)
    assert not is_component_compatible("money_input", {"type": "string"}, catalog)


def test_date_components_compatible_with_string_only() -> None:
    catalog = load_component_catalog()
    assert is_component_compatible("date_picker", {"type": "string"}, catalog)
    assert is_component_compatible("datetime_picker", {"type": "string"}, catalog)
    assert not is_component_compatible("date_picker", {"type": "number"}, catalog)
    assert not is_component_compatible("datetime_picker", {"type": "object"}, catalog)


def test_new_components_present_in_catalog() -> None:
    catalog = load_component_catalog()
    names = {c["name"] for c in catalog["components"]}
    assert {"money_input", "date_picker", "datetime_picker"} <= names
