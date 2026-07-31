"""Port for runtime option providers.

A question may declare an ``option_source`` instead of static ``choices``. At
runtime the engine asks a named provider to resolve that source into an ordered
list of stable ``{"id", "label"}`` choices. Providers are pure lookups: given a
spec they return choices deterministically.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

Choice = dict[str, str]


@runtime_checkable
class OptionProvider(Protocol):
    """Resolves a declared option source into stable choices."""

    @property
    def name(self) -> str:
        """The provider identifier referenced by ``option_source.provider``."""
        ...

    def resolve(self, spec: Mapping[str, Any]) -> list[Choice]:
        """Return an ordered list of ``{"id", "label"}`` choices for *spec*.

        IDs must be stable across calls so answers remain valid over time.
        """
        ...
