"""Integration test for User Story 1 — the complete typed capture loop.

Publishes the shared multi-shape questionnaire and drives a session through a
runtime option source, a nested collection, and money + date/time controls,
asserting each control renders and stores a stable typed value.
"""

from __future__ import annotations

import json
from typing import Any

from httpx import AsyncClient

AUTHOR = json.dumps({"actor_id": "author-1", "roles": ["author"]})
RESPONDENT = json.dumps({"actor_id": "resp-1", "roles": ["respondent"]})


async def _publish(client: AsyncClient, spec: dict[str, Any], *, qs_id: str) -> tuple[str, int]:
    create = await client.post(
        "/api/v1/questionnaire-drafts",
        json={"id": qs_id, "title": f"Test {qs_id}", "output_contract": spec["output_contract"]},
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert create.status_code == 201, create.text

    operations = [{"operation": "upsert_question", "question": q} for q in spec["questions"]]
    patch = await client.patch(
        f"/api/v1/questionnaire-drafts/{qs_id}",
        json={"operations": operations},
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


async def test_capture_loop_over_multi_shape_questionnaire(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    qs_id, version = await _publish(client, multi_shape_questionnaire, qs_id="us1-capture")

    start = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    assert start.status_code == 201, start.text
    view = start.json()
    session_id = view["session"]["id"]

    # Runtime option source: choices load at runtime from the component catalog.
    interaction = view["current_interaction"]
    assert interaction["id"] == "q-component"
    assert interaction["choices"], "runtime options must be resolved onto the interaction"
    choice_ids = [c["id"] for c in interaction["choices"]]
    assert "money_input" in choice_ids
    assert interaction["answer_schema"]["enum"] == choice_ids

    # Answering with a runtime-resolved option is accepted and stored typed.
    view = await _answer(client, session_id, "q-component", "money_input", 1)
    assert view["result"]["data"]["component"] == "money_input"

    # Nested collection projects as a typed array.
    rooms = [{"name": "Kitchen", "area": 200}, {"name": "Bath"}]
    view = await _answer(client, session_id, "q-rooms", rooms, 2)
    assert view["result"]["data"]["rooms"] == rooms

    # Money stored as a typed number.
    budget = 750000
    view = await _answer(client, session_id, "q-budget", budget, 3)
    assert view["result"]["data"]["budget"] == budget

    # Date and date/time stored as typed strings.
    view = await _answer(client, session_id, "q-start", "2026-01-15", 4)
    assert view["result"]["data"]["start_date"] == "2026-01-15"

    view = await _answer(client, session_id, "q-appointment", "2026-01-15T09:30:00Z", 5)
    assert view["result"]["data"]["appointment"] == "2026-01-15T09:30:00Z"


async def test_runtime_option_rejects_unknown_choice(
    client: AsyncClient, multi_shape_questionnaire: dict[str, Any]
) -> None:
    qs_id, version = await _publish(client, multi_shape_questionnaire, qs_id="us1-reject")
    start = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": qs_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    session_id = start.json()["session"]["id"]

    resp = await client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"interaction_id": "q-component", "value": "not-a-component", "expected_revision": 1},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    assert resp.status_code == 422, resp.text
