"""Integration tests for User Story 2 — publication through the JSON document adapter.

Tests idempotent republish, stale revision rejection, not-ready gate, and
outcome_unknown reconciliation (T017, T017a).
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

AUTHOR = json.dumps({"actor_id": "author-1", "roles": ["author"]})
RESPONDENT = json.dumps({"actor_id": "resp-1", "roles": ["respondent"]})
PUBLISHER = json.dumps({"actor_id": "pub-1", "roles": ["publisher"]})


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------


async def _publish_qs(
    client: AsyncClient, spec: dict[str, Any], *, qs_id: str
) -> tuple[str, int]:
    create = await client.post(
        "/api/v1/questionnaire-drafts",
        json={"id": qs_id, "title": f"Test {qs_id}", "output_contract": spec["output_contract"]},
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert create.status_code == 201, create.text

    operations = [{"operation": "upsert_question", "question": q} for q in spec["questions"]]
    patch_resp = await client.patch(
        f"/api/v1/questionnaire-drafts/{qs_id}",
        json={"operations": operations},
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert patch_resp.status_code == 200, patch_resp.text

    publish = await client.post(
        f"/api/v1/questionnaire-drafts/{qs_id}/publish",
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert publish.status_code == 201, publish.text
    data = publish.json()
    return data["questionnaire_id"], data["version"]


async def _start_session(client: AsyncClient, qs_id: str, version: int) -> tuple[str, int]:
    resp = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    assert resp.status_code == 201, resp.text
    view = resp.json()
    return view["session"]["id"], view["session"]["revision"]


async def _answer(
    client: AsyncClient, session_id: str, interaction_id: str, value: Any, revision: int
) -> dict[str, Any]:
    resp = await client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"interaction_id": interaction_id, "value": value, "expected_revision": revision},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Ready-state helper: answer only the required output need (component)
# so the session reaches readiness=ready.
# ---------------------------------------------------------------------------


async def _make_ready(
    client: AsyncClient, spec: dict[str, Any], qs_id: str
) -> tuple[str, int]:
    """Publish a questionnaire, start a session, and answer only the required question."""
    qs_id_full, version = await _publish_qs(client, spec, qs_id=qs_id)
    session_id, _ = await _start_session(client, qs_id_full, version)

    # Answer the required 'component' question to reach readiness=ready.
    view = await _answer(client, session_id, "q-component", "short_text", 1)
    readiness = view["health"]["readiness"]
    assert readiness == "ready", (
        f"Expected readiness='ready' after answering required question, got {readiness!r}. "
        "Review health policy or output contract for the multi_shape_questionnaire fixture."
    )
    return session_id, view["session"]["revision"]


# ---------------------------------------------------------------------------
# T017: idempotent republish, stale revision → 409, gate failure → 422
# ---------------------------------------------------------------------------


async def test_preview_returns_document_without_side_effects(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    session_id, _ = await _make_ready(client, multi_shape_questionnaire, qs_id="pub-preview")

    resp = await client.get(
        f"/api/v1/sessions/{session_id}/result/preview",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert resp.status_code == 200, resp.text
    preview = resp.json()
    assert preview["session_id"] == session_id
    assert preview["adapter"] == "json_document"
    assert "content_hash" in preview
    assert preview["document"]["component"] == "short_text"

    # Preview must have no side effects: no publication artifacts exist yet.
    listing = await client.get(
        f"/api/v1/sessions/{session_id}/publications",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert listing.status_code == 200
    assert listing.json()["publications"] == []


async def test_publish_succeeds_and_returns_receipt(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    session_id, revision = await _make_ready(client, multi_shape_questionnaire, qs_id="pub-ok")

    resp = await client.post(
        f"/api/v1/sessions/{session_id}/publications",
        json={"idempotency_key": "key-1", "expected_revision": revision},
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert resp.status_code == 201, resp.text
    receipt = resp.json()
    assert receipt["status"] == "succeeded"
    assert receipt["session_id"] == session_id
    assert receipt["adapter"] == "json_document"
    assert receipt["publication_id"]

    # Listing shows the one publication.
    listing = await client.get(
        f"/api/v1/sessions/{session_id}/publications",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert listing.json()["publications"][0]["publication_id"] == receipt["publication_id"]


async def test_republish_with_same_key_is_idempotent_no_duplicate(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    session_id, revision = await _make_ready(
        client, multi_shape_questionnaire, qs_id="pub-idempotent"
    )

    first = await client.post(
        f"/api/v1/sessions/{session_id}/publications",
        json={"idempotency_key": "idem-key", "expected_revision": revision},
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/sessions/{session_id}/publications",
        json={"idempotency_key": "idem-key", "expected_revision": revision},
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert second.status_code == 201

    # Same publication_id — no duplicate artifact.
    assert first.json()["publication_id"] == second.json()["publication_id"]

    listing = await client.get(
        f"/api/v1/sessions/{session_id}/publications",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert len(listing.json()["publications"]) == 1


async def test_stale_revision_returns_409(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    session_id, revision = await _make_ready(
        client, multi_shape_questionnaire, qs_id="pub-stale"
    )

    resp = await client.post(
        f"/api/v1/sessions/{session_id}/publications",
        json={"idempotency_key": "stale-key", "expected_revision": revision + 99},
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert resp.status_code == 409, resp.text


async def test_not_ready_session_returns_422(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    """Publishing a session that is not yet ready must be rejected with 422."""
    qs_id, version = await _publish_qs(
        client, multi_shape_questionnaire, qs_id="pub-notready"
    )
    session_id, revision = await _start_session(client, qs_id, version)
    # Do not answer anything — session remains not_ready.

    resp = await client.post(
        f"/api/v1/sessions/{session_id}/publications",
        json={"idempotency_key": "fail-key", "expected_revision": revision},
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert resp.status_code == 422, resp.text


# ---------------------------------------------------------------------------
# T017a: outcome_unknown + reconcile to terminal status without duplicate
# ---------------------------------------------------------------------------


async def test_outcome_unknown_records_receipt_and_reconcile_resolves_it(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    """An indeterminate adapter outcome is recorded as outcome_unknown; reconcile resolves it."""
    from qava.ports.output_adapter import IndeterminateOutcomeError

    session_id, revision = await _make_ready(
        client, multi_shape_questionnaire, qs_id="pub-unknown"
    )

    with patch(
        "qava.infrastructure.adapters.json_document.JsonDocumentAdapter.publish",
        new_callable=AsyncMock,
        side_effect=IndeterminateOutcomeError("Network timeout — outcome uncertain."),
    ):
        resp = await client.post(
            f"/api/v1/sessions/{session_id}/publications",
            json={"idempotency_key": "unk-key", "expected_revision": revision},
            headers={"X-Qava-Identity": PUBLISHER},
        )
    assert resp.status_code == 201, resp.text
    receipt = resp.json()
    pub_id = receipt["publication_id"]
    assert receipt["status"] == "outcome_unknown"

    # No artifact was written.
    listing = await client.get(
        f"/api/v1/sessions/{session_id}/publications",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert listing.json()["publications"][0]["status"] == "outcome_unknown"

    # Reconcile resolves to terminal status without writing a duplicate artifact.
    reconcile = await client.post(
        f"/api/v1/sessions/{session_id}/publications/{pub_id}/reconcile",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert reconcile.status_code == 200, reconcile.text
    resolved = reconcile.json()
    # Adapter has no stored artifact → fails cleanly.
    assert resolved["status"] in {"failed", "succeeded"}

    # Calling reconcile again on a terminal record is a no-op.
    again = await client.post(
        f"/api/v1/sessions/{session_id}/publications/{pub_id}/reconcile",
        headers={"X-Qava-Identity": PUBLISHER},
    )
    assert again.status_code == 200
    assert again.json()["status"] == resolved["status"]
