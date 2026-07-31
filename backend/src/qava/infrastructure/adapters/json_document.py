"""JSON document output adapter.

Writes a ready result as an immutable JSON artifact into Qava's own published
artifact store. Publication is idempotent per ``publication_id`` so republishing
or reconciling never produces a duplicate artifact.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from qava.domain.models import PublicationId, PublishedArtifactRecord, SessionId
from qava.ports.output_adapter import AdapterPreview, AdapterReceipt, AdapterValidation
from qava.ports.repositories import PublishedArtifactRepository

ADAPTER_NAME = "json_document"


def content_hash(document: dict[str, Any]) -> str:
    canonical = json.dumps(document, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def default_destination(session_id: str) -> str:
    return f"qava-store://sessions/{session_id}/artifact"


class JsonDocumentAdapter:
    name = ADAPTER_NAME

    def __init__(self, artifacts: PublishedArtifactRepository) -> None:
        self._artifacts = artifacts

    def validate(self, *, document: dict[str, Any], destination: str) -> AdapterValidation:
        problems: list[str] = []
        if not isinstance(document, dict):
            problems.append("Result document must be a JSON object.")
        elif not document:
            problems.append("Result document is empty; nothing to publish.")
        if not destination:
            problems.append("A publication destination is required.")
        return AdapterValidation(ok=not problems, problems=problems)

    def preview(self, *, document: dict[str, Any], destination: str) -> AdapterPreview:
        return AdapterPreview(
            adapter=self.name,
            destination=destination,
            content_hash=content_hash(document),
            document=document,
        )

    async def publish(
        self,
        *,
        publication_id: str,
        session_id: str,
        session_revision: int,
        document: dict[str, Any],
        destination: str,
    ) -> AdapterReceipt:
        digest = content_hash(document)
        await self._artifacts.put_if_absent(
            PublishedArtifactRecord(
                publication_id=PublicationId(publication_id),
                session_id=SessionId(session_id),
                session_revision=session_revision,
                adapter=self.name,
                destination=destination,
                content_hash=digest,
                document=document,
                created_at=datetime.now(UTC),
            )
        )
        return AdapterReceipt(
            status="succeeded",
            adapter=self.name,
            destination=destination,
            content_hash=digest,
            external_reference=publication_id,
        )

    async def reconcile(self, *, publication_id: str, destination: str) -> AdapterReceipt:
        artifact = await self._artifacts.get(PublicationId(publication_id))
        if artifact is None:
            return AdapterReceipt(
                status="failed",
                adapter=self.name,
                destination=destination,
                content_hash="",
                detail="No artifact was written for this publication.",
            )
        return AdapterReceipt(
            status="succeeded",
            adapter=self.name,
            destination=artifact.destination,
            content_hash=artifact.content_hash,
            external_reference=publication_id,
        )
