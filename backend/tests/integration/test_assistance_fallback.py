"""Integration tests for assistance-mode deterministic fallback."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

from qava.config import get_settings
from qava.domain.models import SessionId
from qava.infrastructure.database.repositories import SQLiteAssistanceProposalRepository

AUTHOR = '{"actor_id": "author-1", "roles": ["author"]}'
RESPONDENT = '{"actor_id": "resp-1", "roles": ["respondent"]}'


def _stable_view(view: dict[str, Any]) -> dict[str, Any]:
    result = dict(view["result"])
    result.pop("session_id", None)
    return {
        "current_interaction": view["current_interaction"],
        "progress": view["progress"],
        "result": result,
        "health": view["health"],
        "actions": view["actions"],
    }


async def _start_session(
    client: AsyncClient, questionnaire_id: str, version: int
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/sessions",
        json={"questionnaire_id": questionnaire_id, "questionnaire_version": version},
        headers={"X-Qava-Identity": RESPONDENT},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _publish_two_question_qs(client: AsyncClient, *, qs_id: str) -> tuple[str, int]:
    create = await client.post(
        "/api/v1/questionnaire-drafts",
        json={
            "id": qs_id,
            "title": "Assistance fallback",
            "output_contract": {
                "type": "object",
                "properties": {"required": {"type": "string"}},
                "required": ["required"],
            },
        },
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert create.status_code == 201, create.text
    operations: list[dict[str, Any]] = [
        {
            "operation": "upsert_question",
            "question": {
                "id": "required-answer",
                "topic_id": "fallback",
                "prompt": "Provide the required answer.",
                "output_need_ids": ["need:required"],
                "answer_schema": {"type": "string"},
                "mapping": {"mode": "direct", "target": "/required"},
                "presentation": {"name": "short_text", "version": 1, "props": {}},
                "required": True,
                "order": 1,
            },
        }
    ]
    update = await client.patch(
        f"/api/v1/questionnaire-drafts/{qs_id}",
        json={"operations": operations},
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert update.status_code == 200, update.text
    publish = await client.post(
        f"/api/v1/questionnaire-drafts/{qs_id}/publish",
        headers={"X-Qava-Identity": AUTHOR},
    )
    assert publish.status_code == 201, publish.text
    result = publish.json()
    return result["questionnaire_id"], result["version"]


async def test_fixture_mode_preserves_deterministic_fallback(
    client: AsyncClient,
    in_memory_manager: Any,
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("QAVA_ASSISTANCE_MODE", "fixture")
    get_settings.cache_clear()
    fixture_questionnaire, fixture_version = await _publish_two_question_qs(
        client, qs_id="fixture-fallback"
    )
    fixture_view = await _start_session(client, fixture_questionnaire, fixture_version)

    async with in_memory_manager.session() as database_session:
        proposals = SQLiteAssistanceProposalRepository(database_session)
        records = await proposals.list_for_session(SessionId(fixture_view["session"]["id"]))
    assert len(records) == 1
    assert records[0]["operation"] == "ranking"
    assert records[0]["status"] == "rejected"
    assert records[0]["payload"] == {"reason": "disabled_or_not_permitted"}

    monkeypatch.setenv("QAVA_ASSISTANCE_MODE", "disabled")
    get_settings.cache_clear()
    disabled_questionnaire, disabled_version = await _publish_two_question_qs(
        client, qs_id="disabled-fallback"
    )
    disabled_view = await _start_session(client, disabled_questionnaire, disabled_version)

    assert _stable_view(fixture_view) == _stable_view(disabled_view)
    get_settings.cache_clear()