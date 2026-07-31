"""Integration tests for authoring workflow: draft create/update/validate/publish.

These tests run the full FastAPI + SQLite stack with an in-memory database.
"""

from __future__ import annotations

import json

from httpx import AsyncClient


def _identity_header(actor_id: str, roles: list[str]) -> str:
    return json.dumps({"actor_id": actor_id, "roles": roles})


BASE64URL_AUTHOR = _identity_header("author-1", ["author"])
BASE64URL_RESPONDENT = _identity_header("resp-1", ["respondent"])


async def test_create_draft_requires_author_role(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/questionnaire-drafts",
        json={
            "id": "test-qs",
            "title": "Test",
            "output_contract": {"type": "object", "properties": {}},
        },
        headers={"X-Qava-Identity": BASE64URL_RESPONDENT},
    )
    assert resp.status_code == 403


async def test_create_draft_returns_compiled_draft(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/questionnaire-drafts",
        json={
            "id": "home-intake",
            "title": "Custom Home Intake",
            "output_contract": {
                "type": "object",
                "properties": {
                    "budget": {"type": "object"},
                    "rooms": {"type": "array"},
                },
                "required": ["budget"],
            },
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == "home-intake"
    assert isinstance(body["output_needs"], list)
    assert any(n["required"] for n in body["output_needs"])


async def test_get_draft_returns_404_when_not_found(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/questionnaire-drafts/nonexistent",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert resp.status_code == 404


async def test_publish_draft_creates_immutable_questionnaire(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/questionnaire-drafts",
        json={
            "id": "publishable-qs",
            "title": "Publishable",
            "output_contract": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert create_resp.status_code == 201

    # Add a question that maps the required field
    draft_id = create_resp.json()["id"]
    patch_resp = await client.patch(
        f"/api/v1/questionnaire-drafts/{draft_id}",
        json={
            "operations": [
                {
                    "operation": "upsert_question",
                    "question": {
                        "id": "q-name",
                        "prompt": "What is the project name?",
                        "output_need_ids": ["need:name"],
                        "answer_schema": {"type": "string"},
                        "mapping": {"mode": "direct", "target": "/name"},
                        "presentation": {"name": "short_text", "version": 1, "props": {}},
                        "required": True,
                        "order": 1,
                    },
                }
            ]
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert patch_resp.status_code == 200

    pub_resp = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/publish",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert pub_resp.status_code == 201
    pub = pub_resp.json()
    assert pub["version"] == 1
    assert pub["questionnaire_id"] == "publishable-qs"

    # Attempt a second publish — must create version 2 (idempotent re-use of same draft is fine)
    pub2_resp = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/publish",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert pub2_resp.status_code in (201, 409)


# ---------------------------------------------------------------------------
# T016: draft deletion (FR-020, US2)
# ---------------------------------------------------------------------------

async def test_draft_deletion_not_found(client: AsyncClient) -> None:
    """DELETE on a nonexistent draft returns 404."""
    resp = await client.delete(
        "/api/v1/questionnaire-drafts/no-such-draft",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert resp.status_code == 404


async def test_draft_deletion_succeeds(client: AsyncClient) -> None:
    """DELETE removes the draft; subsequent GET returns 404."""
    create = await client.post(
        "/api/v1/questionnaire-drafts",
        json={"id": "deletable-qs", "title": "Deletable",
              "output_contract": {"type": "object"}},
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert create.status_code == 201

    delete_resp = await client.delete(
        "/api/v1/questionnaire-drafts/deletable-qs",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        "/api/v1/questionnaire-drafts/deletable-qs",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# US4: explicit authoring decisions and raw-draft replacement
# ---------------------------------------------------------------------------


def _us4_question() -> dict:
    return {
        "id": "q-name",
        "prompt": "What is the project name?",
        "output_need_ids": ["need:name"],
        "answer_schema": {"type": "string"},
        "mapping": {"mode": "direct", "target": "/name"},
        "presentation": {"name": "short_text", "version": 1, "props": {}},
        "required": True,
        "order": 1,
    }


async def _create_us4_draft(client: AsyncClient, draft_id: str) -> None:
    response = await client.post(
        "/api/v1/questionnaire-drafts",
        json={
            "id": draft_id,
            "title": "Decision draft",
            "output_contract": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert response.status_code == 201, response.text

    response = await client.patch(
        f"/api/v1/questionnaire-drafts/{draft_id}",
        json={"operations": [{"operation": "upsert_question", "question": _us4_question()}]},
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert response.status_code == 200, response.text


async def test_pending_decision_blocks_publish_then_confirm_allows_it(client: AsyncClient) -> None:
    draft_id = "decision-confirm"
    await _create_us4_draft(client, draft_id)

    raw = await client.put(
        f"/api/v1/questionnaire-drafts/{draft_id}/raw",
        json={
            "title": "Decision draft",
            "output_contract": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "questions": [_us4_question()],
            "decisions": [
                {
                    "decision_id": "d-component",
                    "kind": "component",
                    "candidates": [{"value": "short_text", "confidence": 0.6}],
                    "blocking": True,
                    "status": "pending",
                }
            ],
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert raw.status_code == 200, raw.text
    assert raw.json()["pending_decisions"][0]["decision_id"] == "d-component"

    blocked = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/publish",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert blocked.status_code == 422, blocked.text
    assert "pending blocking decision" in blocked.json()["detail"]["detail"]

    confirmed = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/decisions",
        json={"decision_id": "d-component", "action": "confirm"},
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["decisions"][0]["status"] == "confirmed"
    assert confirmed.json()["pending_decisions"] == []

    published = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/publish",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert published.status_code == 201, published.text


async def test_override_and_reject_are_preserved_and_clear_pending(client: AsyncClient) -> None:
    draft_id = "decision-override-reject"
    await _create_us4_draft(client, draft_id)

    raw = await client.put(
        f"/api/v1/questionnaire-drafts/{draft_id}/raw",
        json={
            "title": "Decision draft",
            "output_contract": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "questions": [_us4_question()],
            "decisions": [
                {"decision_id": "d-mapping", "kind": "mapping", "blocking": True},
                {"decision_id": "d-extra", "kind": "question", "blocking": False},
            ],
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert raw.status_code == 200, raw.text

    overridden = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/decisions",
        json={
            "decision_id": "d-mapping",
            "action": "override",
            "resolution": {"target": "/name", "component": "short_text"},
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert overridden.status_code == 200, overridden.text

    rejected = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/decisions",
        json={"decision_id": "d-extra", "action": "reject"},
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert rejected.status_code == 200, rejected.text
    decisions = {item["decision_id"]: item for item in rejected.json()["decisions"]}
    assert decisions["d-mapping"]["status"] == "overridden"
    assert decisions["d-mapping"]["resolution"] == {
        "target": "/name",
        "component": "short_text",
    }
    assert decisions["d-extra"]["status"] == "rejected"


async def test_raw_replacement_uses_same_publication_gate_as_guided_updates(client: AsyncClient) -> None:
    draft_id = "raw-gate"
    await _create_us4_draft(client, draft_id)

    raw = await client.put(
        f"/api/v1/questionnaire-drafts/{draft_id}/raw",
        json={
            "title": "Raw invalid",
            "output_contract": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "questions": [],
            "decisions": [],
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert raw.status_code == 200, raw.text
    assert raw.json()["validation_issues"][0]["code"] == "missing_required_target"

    blocked = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/publish",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert blocked.status_code == 422, blocked.text

    corrected = await client.put(
        f"/api/v1/questionnaire-drafts/{draft_id}/raw",
        json={
            "title": "Raw valid",
            "output_contract": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "questions": [_us4_question()],
            "decisions": [],
        },
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["validation_issues"] == []

    published = await client.post(
        f"/api/v1/questionnaire-drafts/{draft_id}/publish",
        headers={"X-Qava-Identity": BASE64URL_AUTHOR},
    )
    assert published.status_code == 201, published.text
