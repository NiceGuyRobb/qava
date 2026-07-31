"""Runtime option providers and their registry."""

from __future__ import annotations

from qava.infrastructure.options.component_catalog import (
    ComponentCatalogOptionProvider,
    load_component_catalog,
)
from qava.infrastructure.options.registry import (
    OptionProviderRegistry,
    UnknownOptionProviderError,
    default_option_provider_registry,
)

__all__ = [
    "ComponentCatalogOptionProvider",
    "OptionProviderRegistry",
    "UnknownOptionProviderError",
    "default_option_provider_registry",
    "load_component_catalog",
]
