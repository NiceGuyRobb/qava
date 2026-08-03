"""Contract tests for the self-hosted registry publication adapter (US5)."""

from __future__ import annotations

import pytest

from qava.domain.models import PublishedQuestionnaireRecord, QuestionnaireId
from qava.infrastructure.adapters.registry import RegistryAdapter


class _Repository:
    def __init__(self) -> None:
        self.records: list[PublishedQuestionnaireRecord] = []

    async def insert(self, record: PublishedQuestionnaireRecord) -> None:
        self.records.append(record)

    async def get(self, questionnaire_id: QuestionnaireId, version: int) -> PublishedQuestionnaireRecord | None:
        return next(
            (record for record in self.records if record.questionnaire_id == questionnaire_id and record.version == version),
            None,
        )

    async def get_latest_version(self, questionnaire_id: QuestionnaireId) -> int | None:
        versions = [record.version for record in self.records if record.questionnaire_id == questionnaire_id]
        return max(versions) if versions else None


def _document() -> dict:
    return {
        "id": "meta-authored",
        "title": "Meta authored questionnaire",
        "output_contract": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        "questions": [
            {
                "id": "q-name",
                "prompt": "What is the name?",
                "output_need_ids": ["need:name"],
                "answer_schema": {"type": "string"},
                "mapping": {"mode": "direct", "target": "/name"},
                "presentation": {"name": "short_text", "version": 1, "props": {}},
                "required": True,
                "order": 1,
            }
        ],
    }


@pytest.mark.asyncio
async def test_registry_receipt_returns_immutable_questionnaire_identity() -> None:
    repository = _Repository()
    adapter = RegistryAdapter(repository)
    document = _document()

    assert adapter.validate(document=document, destination="registry://questionnaires").ok
    receipt = await adapter.publish(
        publication_id="publication-1",
        session_id="session-1",
        session_revision=4,
        document=document,
        destination="registry://questionnaires",
    )

    assert receipt.status == "succeeded"
    assert receipt.external_reference == "questionnaire:meta-authored@1"
    assert len(repository.records) == 1
    assert repository.records[0].version == 1


@pytest.mark.asyncio
async def test_registry_publication_creates_new_immutable_version() -> None:
    repository = _Repository()
    adapter = RegistryAdapter(repository)
    document = _document()

    await adapter.publish(
        publication_id="publication-1",
        session_id="session-1",
        session_revision=4,
        document=document,
        destination="registry://questionnaires",
    )
    receipt = await adapter.publish(
        publication_id="publication-2",
        session_id="session-2",
        session_revision=5,
        document=document,
        destination="registry://questionnaires",
    )

    assert receipt.external_reference == "questionnaire:meta-authored@2"
    assert [record.version for record in repository.records] == [1, 2]


def test_registry_rejects_invalid_questionnaire_document() -> None:
    adapter = RegistryAdapter(_Repository())
    validation = adapter.validate(document={"id": "missing-fields"}, destination="registry://questionnaires")
    assert not validation.ok
    assert validation.problems
