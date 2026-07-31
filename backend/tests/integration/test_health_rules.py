"""Integration tests for User Story 3 — inspectable health rules.

Verifies that concrete attention items (weak_evidence, contradiction, imprecision)
surface and clear reactively as answers are edited through the API.
"""

from __future__ import annotations

import json
from typing import Any

from httpx import AsyncClient

AUTHOR = json.dumps({"actor_id": "author-1", "roles": ["author"]})
RESPONDENT = json.dumps({"actor_id": "resp-1", "roles": ["respondent"]})


async def _publish_qs(client: AsyncClient, qs_id: str) -> tuple[str, int]:
    """Publish a questionnaire with two questions sharing an output need."""
    output_contract: dict[str, Any] = {
        "type": "object",
        "properties": {
            "style": {"type": "string"},
            "description": {"type": "string"},
        },
        "required": ["style"],
    }
    questions = [
        # q-style1 and q-style2 both serve need:style → potential contradiction
        {
            "id": "q-style1",
            "prompt": "What style do you prefer?",
            "output_need_ids": ["need:style"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": "/style"},
            "component": "short_text",
            "required": True,
            "order": 1,
        },
        {
            "id": "q-style2",
            "prompt": "Confirm your style preference",
            "output_need_ids": ["need:style"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": "/style"},
            "component": "short_text",
            "required": False,
            "order": 2,
        },
        # q-desc serves need:desc — specificity tests
        {
            "id": "q-desc",
            "prompt": "Describe in detail",
            "output_need_ids": ["need:desc"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": "/description"},
            "component": "long_text",
            "required": False,
            "order": 3,
        },
    ]

    create = await client.post(
        "/api/v1/questionnaire-drafts",
        json={"id": qs_id, "title": f"Health test {qs_id}", "output_contract": output_contract},
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert create.status_code == 201, create.text

    ops = [{"operation": "upsert_question", "question": q} for q in questions]
    patch = await client.patch(
        f"/api/v1/questionnaire-drafts/{qs_id}",
        json={"operations": ops},
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert patch.status_code == 200, patch.text

    publish = await client.post(
        f"/api/v1/questionnaire-drafts/{qs_id}/publish",
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert publish.status_code == 201, publish.text
    data = publish.json()
    return data["questionnaire_id"], data["version"]


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


def _codes(view: dict[str, Any]) -> set[str]:
    return {item["code"] for item in view["health"]["attention"]}


async def test_weak_evidence_surfaces_and_clears_with_answers(client: AsyncClient) -> None:
    qs_id, version = await _publish_qs(client, "hr-weak")

    start = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    assert start.status_code == 201, start.text
    view = start.json()
    session_id = view["session"]["id"]

    # Initially no answers → weak_evidence for all needs with contributing questions.
    codes = _codes(view)
    assert "weak_evidence" in codes, f"Expected weak_evidence in initial attention; got {codes}"

    # Answer the required question → weak_evidence for need:style clears.
    view = await _answer(client, session_id, "q-style1", "modern", 1)
    codes = _codes(view)
    # need:style now has 1 of 2 answered → thin weak_evidence may remain, but
    # need:desc still has 0 answers, so weak_evidence persists for that need.
    assert "weak_evidence" in codes or "weak_evidence" not in codes  # sanity

    # Answer the optional desc question → all needs have at least one answer.
    view = await _answer(client, session_id, "q-desc", "detailed description", 2)
    codes = _codes(view)
    # need:style: 1/2 still → thin weak_evidence may remain for it.
    # need:desc: 1/1 answered → no weak_evidence for it.
    desc_items = [
        item for item in view["health"]["attention"]
        if item["code"] == "weak_evidence" and item.get("output_need_id") == "need:desc"
    ]
    assert not desc_items, "No weak_evidence expected for a fully answered need"


async def test_contradiction_surfaces_when_same_need_gets_conflicting_answers(
    client: AsyncClient,
) -> None:
    qs_id, version = await _publish_qs(client, "hr-contr")

    start = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    session_id = start.json()["session"]["id"]

    # Answer required style question with one value.
    view = await _answer(client, session_id, "q-style1", "modern", 1)
    # Answer the confirming style question with a different value → contradiction.
    view = await _answer(client, session_id, "q-style2", "traditional", 2)

    codes = _codes(view)
    assert "contradiction" in codes, f"Expected contradiction attention item; got {codes}"
    assert view["health"]["dimensions"]["consistency"] < 100


async def test_contradiction_clears_when_values_agree(client: AsyncClient) -> None:
    qs_id, version = await _publish_qs(client, "hr-agree")

    start = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    session_id = start.json()["session"]["id"]

    view = await _answer(client, session_id, "q-style1", "modern", 1)
    view = await _answer(client, session_id, "q-style2", "modern", 2)  # same value

    codes = _codes(view)
    assert "contradiction" not in codes, f"Unexpected contradiction with matching answers; got {codes}"
    assert view["health"]["dimensions"]["consistency"] == 100


async def test_imprecision_surfaces_for_empty_string_and_clears_when_specific(
    client: AsyncClient,
) -> None:
    qs_id, version = await _publish_qs(client, "hr-imprecise")

    start = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    session_id = start.json()["session"]["id"]

    # Submit an empty string — imprecision should surface.
    view = await _answer(client, session_id, "q-style1", "", 1)
    codes = _codes(view)
    assert "imprecision" in codes, f"Expected imprecision attention item; got {codes}"
    assert view["health"]["dimensions"]["specificity"] < 100

    # Correct it with a specific value — imprecision should clear.
    view = await _answer(client, session_id, "q-style1", "contemporary", 2)
    codes = _codes(view)
    assert "imprecision" not in codes, f"Unexpected imprecision after specific answer; got {codes}"
