"""Registry mapping option-source provider names to providers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from qava.infrastructure.options.component_catalog import ComponentCatalogOptionProvider
from qava.ports.option_provider import Choice, OptionProvider


class UnknownOptionProviderError(LookupError):
    """Raised when an option source references an unregistered provider."""


class OptionProviderRegistry:
    def __init__(self, providers: Iterable[OptionProvider]) -> None:
        self._by_name: dict[str, OptionProvider] = {p.name: p for p in providers}

    def resolve(self, spec: Mapping[str, Any]) -> list[Choice]:
        provider_name = spec.get("provider")
        if not isinstance(provider_name, str):
            raise UnknownOptionProviderError("option_source is missing a 'provider'.")
        provider = self._by_name.get(provider_name)
        if provider is None:
            raise UnknownOptionProviderError(f"No option provider named {provider_name!r}.")
        return provider.resolve(spec)


def default_option_provider_registry() -> OptionProviderRegistry:
    """The default registry with the component-catalog provider registered."""
    return OptionProviderRegistry([ComponentCatalogOptionProvider()])
