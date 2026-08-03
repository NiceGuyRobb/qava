"""Integration coverage for the bootstrapped self-hosted authoring flow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from httpx import AsyncClient

from qava.infrastructure.contracts.definition_pack import load_definition_pack

IDENTITY = json.dumps(
    {"actor_id": "meta-author", "roles": ["author", "respondent", "publisher"]}
)
HEADERS = {"X-Qava-Identity": IDENTITY}
META_MANIFEST = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "definitions"
    / "meta"
    / "v1"
    / "definition.json"
)


def _five_question_document() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    properties = {f"answer_{index}": {"type": "string"} for index in range(1, 6)}
    output_contract = {
        "type": "object",
        "properties": properties,
        "required": list(properties),
    }
    questions = [
        {
            "id": f"question-{index}",
            "topic_id": "questions",
            "prompt": f"Provide answer {index}.",
            "output_need_ids": [f"need:answer_{index}"],
            "answer_schema": {"type": "string"},
            "mapping": {"mode": "direct", "target": f"/answer_{index}"},
            "presentation": {"name": "short_text", "version": 1, "props": {}},
            "required": True,
            "order": index,
        }
        for index in range(1, 6)
    ]
    return output_contract, questions


async def _bootstrap_meta_questionnaire(client: AsyncClient) -> None:
    pack = load_definition_pack(META_MANIFEST)
    create = await client.post(
        "/api/v1/questionnaire-drafts",
        json={
            "id": pack.questionnaire_id,
            "title": pack.title,
            "description": pack.description,
            "output_contract": pack.output_contract,
        },
        headers=HEADERS,
    )
    assert create.status_code == 201, create.text

    update = await client.patch(
        f"/api/v1/questionnaire-drafts/{pack.questionnaire_id}",
        json={
            "operations": [
                {"operation": "upsert_question", "question": question}
                for question in pack.questions
            ]
        },
        headers=HEADERS,
    )
    assert update.status_code == 200, update.text

    publish = await client.post(
        f"/api/v1/questionnaire-drafts/{pack.questionnaire_id}/publish",
        headers=HEADERS,
    )
    assert publish.status_code == 201, publish.text


async def test_meta_questionnaire_authors_publishes_and_runs_five_questions(
    client: AsyncClient,
) -> None:
    await _bootstrap_meta_questionnaire(client)

    start_meta = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": "meta-questionnaire", "questionnaire_version": 1},
        headers=HEADERS,
    )
    assert start_meta.status_code == 201, start_meta.text
    meta_view = start_meta.json()
    meta_session_id = meta_view["session"]["id"]
    revision = meta_view["session"]["revision"]
    target_contract, target_questions = _five_question_document()

    for interaction_id, value in (
        ("questionnaire-id", "authored-five-question"),
        ("questionnaire-title", "Authored Five Question Questionnaire"),
        ("output-contract", target_contract),
        ("question-list", target_questions),
    ):
        answer = await client.post(
            f"/api/v1/sessions/{meta_session_id}/answers",
            json={
                "interaction_id": interaction_id,
                "value": value,
                "expected_revision": revision,
            },
            headers=HEADERS,
        )
        assert answer.status_code == 200, answer.text
        meta_view = answer.json()
        revision = meta_view["session"]["revision"]

    assert meta_view["health"]["readiness"] == "ready"
    assert meta_view["result"]["data"]["questions"] == target_questions

    registry_publish = await client.post(
        f"/api/v1/sessions/{meta_session_id}/publications",
        json={
            "idempotency_key": "author-five-question",
            "expected_revision": revision,
            "adapter": "registry",
        },
        headers=HEADERS,
    )
    assert registry_publish.status_code == 201, registry_publish.text
    receipt = registry_publish.json()
    assert receipt["adapter"] == "registry"
    assert receipt["external_reference"] == "questionnaire:authored-five-question@1"

    start_authored = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": "authored-five-question", "questionnaire_version": 1},
        headers=HEADERS,
    )
    assert start_authored.status_code == 201, start_authored.text
    authored_view = start_authored.json()
    authored_session_id = authored_view["session"]["id"]
    revision = authored_view["session"]["revision"]

    for index in range(1, 6):
        answer = await client.post(
            f"/api/v1/sessions/{authored_session_id}/answers",
            json={
                "interaction_id": f"question-{index}",
                "value": f"value-{index}",
                "expected_revision": revision,
            },
            headers=HEADERS,
        )
        assert answer.status_code == 200, answer.text
        authored_view = answer.json()
        revision = authored_view["session"]["revision"]

    assert authored_view["health"]["readiness"] == "ready"
    assert authored_view["result"]["data"] == {
        f"answer_{index}": f"value-{index}" for index in range(1, 6)
    }