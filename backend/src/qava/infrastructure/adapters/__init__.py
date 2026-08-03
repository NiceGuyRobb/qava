"""Output adapters that publish ready results through explicit boundaries."""

from qava.infrastructure.adapters.json_document import (
    ADAPTER_NAME,
    JsonDocumentAdapter,
    content_hash,
    default_destination,
)
from qava.infrastructure.adapters.registry import RegistryAdapter

__all__ = [
    "ADAPTER_NAME",
    "JsonDocumentAdapter",
    "RegistryAdapter",
    "content_hash",
    "default_destination",
]
