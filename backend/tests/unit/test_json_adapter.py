"""Unit tests for the JSON document output adapter (US2)."""

from __future__ import annotations

from typing import Any

import pytest

from qava.domain.models import PublicationId, PublishedArtifactRecord, SessionId
from qava.infrastructure.adapters.json_document import JsonDocumentAdapter, content_hash


class _FakeArtifacts:
    def __init__(self) -> None:
        self.store: dict[str, PublishedArtifactRecord] = {}

    async def put_if_absent(self, record: PublishedArtifactRecord) -> bool:
        key = str(record.publication_id)
        if key in self.store:
            return False
        self.store[key] = record
        return True

    async def get(self, publication_id: PublicationId) -> PublishedArtifactRecord | None:
        return self.store.get(str(publication_id))

    async def count_for_session(self, session_id: SessionId) -> int:
        return sum(1 for r in self.store.values() if r.session_id == session_id)


def test_content_hash_is_key_order_independent() -> None:
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_validate_rejects_empty_or_bad_documents() -> None:
    adapter = JsonDocumentAdapter(_FakeArtifacts())
    assert adapter.validate(document={"x": 1}, destination="dest").ok
    empty = adapter.validate(document={}, destination="dest")
    assert not empty.ok
    assert empty.problems
    no_dest = adapter.validate(document={"x": 1}, destination="")
    assert not no_dest.ok


def test_preview_is_side_effect_free() -> None:
    artifacts = _FakeArtifacts()
    adapter = JsonDocumentAdapter(artifacts)
    document: dict[str, Any] = {"budget": 750000}
    preview = adapter.preview(document=document, destination="dest")
    assert preview.adapter == "json_document"
    assert preview.content_hash == content_hash(document)
    assert preview.document == document
    assert artifacts.store == {}


@pytest.mark.asyncio
async def test_publish_writes_immutable_artifact_and_is_idempotent() -> None:
    artifacts = _FakeArtifacts()
    adapter = JsonDocumentAdapter(artifacts)
    document = {"budget": 750000}

    receipt = await adapter.publish(
        publication_id="pub-1",
        session_id="sess-1",
        session_revision=3,
        document=document,
        destination="dest",
    )
    assert receipt.status == "succeeded"
    assert receipt.external_reference == "pub-1"
    assert receipt.content_hash == content_hash(document)
    assert await artifacts.count_for_session(SessionId("sess-1")) == 1

    # Republishing the same publication id never duplicates the artifact.
    await adapter.publish(
        publication_id="pub-1",
        session_id="sess-1",
        session_revision=3,
        document=document,
        destination="dest",
    )
    assert await artifacts.count_for_session(SessionId("sess-1")) == 1


@pytest.mark.asyncio
async def test_reconcile_resolves_from_the_store() -> None:
    artifacts = _FakeArtifacts()
    adapter = JsonDocumentAdapter(artifacts)

    missing = await adapter.reconcile(publication_id="pub-x", destination="dest")
    assert missing.status == "failed"

    await adapter.publish(
        publication_id="pub-2",
        session_id="sess-1",
        session_revision=1,
        document={"x": 1},
        destination="dest",
    )
    resolved = await adapter.reconcile(publication_id="pub-2", destination="dest")
    assert resolved.status == "succeeded"
    assert resolved.external_reference == "pub-2"
