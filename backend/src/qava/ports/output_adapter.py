"""Output adapter port: validate, preview, publish, and reconcile a result document.

An output adapter is the explicit boundary through which a ready result leaves
Qava. Adapters never mutate the session; publication is the only side effect and
it is expected to be idempotent for a given ``publication_id``.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

AdapterOutcome = Literal["succeeded", "outcome_unknown", "failed"]


class AdapterValidation(BaseModel):
    ok: bool
    problems: list[str] = Field(default_factory=list)


class AdapterPreview(BaseModel):
    adapter: str
    destination: str
    content_hash: str
    document: dict[str, Any]


class AdapterReceipt(BaseModel):
    status: AdapterOutcome
    adapter: str
    destination: str
    content_hash: str
    external_reference: str | None = None
    detail: str | None = None


class IndeterminateOutcomeError(Exception):
    """Raised by an adapter when the terminal outcome cannot be determined.

    The publication is recorded as ``outcome_unknown`` and must be resolved via
    :meth:`OutputAdapter.reconcile`.
    """


@runtime_checkable
class OutputAdapter(Protocol):
    """Resolves a ready result document into an external artifact."""

    @property
    def name(self) -> str:
        """The adapter identifier recorded on the publication attempt."""
        ...

    def validate(self, *, document: dict[str, Any], destination: str) -> AdapterValidation:
        """Check that *document* can be published to *destination* without side effects."""
        ...

    def preview(self, *, document: dict[str, Any], destination: str) -> AdapterPreview:
        """Return the exact artifact that would be published, without side effects."""
        ...

    async def publish(
        self,
        *,
        publication_id: str,
        session_id: str,
        session_revision: int,
        document: dict[str, Any],
        destination: str,
    ) -> AdapterReceipt:
        """Write an immutable artifact for *publication_id* (idempotent)."""
        ...

    async def reconcile(self, *, publication_id: str, destination: str) -> AdapterReceipt:
        """Resolve an ``outcome_unknown`` publication to a terminal receipt."""
        ...
