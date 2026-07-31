"""Registry output adapter for self-hosted questionnaire authoring."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from qava.domain.definition import compile_draft, validate_publication
from qava.domain.models import AssistancePolicy, HealthPolicy, PublishedQuestionnaireRecord, QuestionnaireId
from qava.infrastructure.adapters.json_document import content_hash
from qava.ports.output_adapter import AdapterPreview, AdapterReceipt, AdapterValidation
from qava.ports.repositories import PublishedQuestionnaireRepository

ADAPTER_NAME = "registry"


class RegistryAdapter:
    name = ADAPTER_NAME

    def __init__(self, questionnaires: PublishedQuestionnaireRepository) -> None:
        self._questionnaires = questionnaires

    def validate(self, *, document: dict[str, Any], destination: str) -> AdapterValidation:
        problems: list[str] = []
        questionnaire_id = document.get("id")
        title = document.get("title")
        contract = document.get("output_contract")
        questions = document.get("questions")
        if not isinstance(questionnaire_id, str) or not questionnaire_id.strip():
            problems.append("Questionnaire document requires a non-empty id.")
        if not isinstance(title, str) or not title.strip():
            problems.append("Questionnaire document requires a non-empty title.")
        if not isinstance(contract, dict):
            problems.append("Questionnaire document requires an output_contract object.")
        if not isinstance(questions, list) or not all(isinstance(question, dict) for question in questions):
            problems.append("Questionnaire document requires a questions array of objects.")
        elif isinstance(questions, list):
            problems.extend(_question_problems(questions))
        if isinstance(contract, dict) and isinstance(questions, list):
            problems.extend(issue.message for issue in validate_publication(
                output_contract=contract,
                questions=_normalized_questions(questions),
            ))
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
        questionnaire_id = QuestionnaireId(str(document["id"]))
        next_version = (await self._questionnaires.get_latest_version(questionnaire_id) or 0) + 1
        contract = document.get("output_contract")
        questions = document.get("questions")
        if not isinstance(contract, dict) or not isinstance(questions, list):
            raise ValueError("Registry publication requires a validated questionnaire document.")
        normalized_questions = _normalized_questions(questions)
        compiled = compile_draft(
            draft_id=str(questionnaire_id),
            title=str(document["title"]),
            output_contract=contract,
            questions=normalized_questions,
        )
        payload_hash = hashlib.sha256(
            json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        record = PublishedQuestionnaireRecord(
            questionnaire_id=questionnaire_id,
            version=next_version,
            title=str(document["title"]),
            output_contract=contract,
            output_needs=compiled["output_needs"],
            questions=normalized_questions,
            health_policy=HealthPolicy.model_validate(document.get("health_policy", _default_health_policy())),
            assistance_policy=AssistancePolicy.model_validate(
                document.get("assistance_policy", _default_assistance_policy())
            ),
            content_hash=payload_hash,
            published_by=f"publication:{publication_id}",
            published_at=datetime.now(UTC),
        )
        await self._questionnaires.insert(record)
        reference = f"questionnaire:{questionnaire_id}@{next_version}"
        return AdapterReceipt(
            status="succeeded",
            adapter=self.name,
            destination=destination,
            content_hash=content_hash(document),
            external_reference=reference,
        )

    async def reconcile(self, *, publication_id: str, destination: str) -> AdapterReceipt:
        return AdapterReceipt(
            status="failed",
            adapter=self.name,
            destination=destination,
            content_hash="",
            detail="Registry publications are synchronous and cannot have an indeterminate outcome.",
        )


def _default_health_policy() -> dict[str, Any]:
    return {
        "calculation_version": 1,
        "completeness_weight": 1.0,
        "validity_weight": 1.0,
        "confidence_weight": 1.0,
        "consistency_weight": 1.0,
        "specificity_weight": 1.0,
        "minimum_validity": 0,
        "block_on": "blocking",
    }


def _default_assistance_policy() -> dict[str, Any]:
    return {
        "enabled_operations": [],
        "maximum_clarifications_per_interaction": 0,
        "maximum_generated_interactions_per_session": 0,
        "timeout_ms": 5000,
        "require_extraction_confirmation": True,
    }


def _question_problems(questions: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question.get("id"), str) or not question["id"].strip():
            problems.append(f"Question {index} requires a non-empty id.")
        if not isinstance(question.get("prompt"), str) or not question["prompt"].strip():
            problems.append(f"Question {index} requires a non-empty prompt.")
        answer_schema = question.get("answer_schema")
        if not isinstance(answer_schema, dict) or not isinstance(answer_schema.get("type"), str):
            problems.append(f"Question {index} requires an answer_schema type.")
        mapping = question.get("mapping")
        if not isinstance(mapping, dict) or mapping.get("mode") != "direct":
            problems.append(f"Question {index} requires a direct mapping.")
        elif not isinstance(mapping.get("target"), str) or not mapping["target"].startswith("/"):
            problems.append(f"Question {index} requires a mapping target.")
        presentation = question.get("presentation")
        if not isinstance(presentation, dict) or not isinstance(presentation.get("name"), str):
            problems.append(f"Question {index} requires a presentation name.")
    return problems


def _normalized_questions(questions: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            continue
        normalized_question = dict(question)
        mapping = normalized_question.get("mapping")
        target = mapping.get("target") if isinstance(mapping, dict) else ""
        target_root = target.split("/", 2)[1] if isinstance(target, str) and target.startswith("/") else ""
        normalized_question.setdefault("topic_id", "authored")
        normalized_question.setdefault(
            "output_need_ids", [f"need:{target_root}"] if target_root else []
        )
        normalized_question.setdefault("required", True)
        normalized_question.setdefault("order", index)
        presentation = normalized_question.get("presentation")
        if isinstance(presentation, dict):
            normalized_question["presentation"] = {
                "version": 1,
                "props": {},
                **presentation,
            }
        normalized.append(normalized_question)
    return normalized
