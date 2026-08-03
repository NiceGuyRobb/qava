"""Questionnaire drafts and published questionnaires API router."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from qava.api.dependencies import (
    IdentityContext,
    get_authoring_service,
    require_author,
)
from qava.api.errors import not_found_problem, validation_problem
from qava.api.schemas import (
    CreateDraftRequest,
    RawDraftRequest,
    ResolveDecisionRequest,
    UpdateDraftRequest,
)
from qava.application.authoring import AuthoringService

router = APIRouter(prefix="/api/v1", tags=["questionnaires"])

AuthorDep = Annotated[IdentityContext, Depends(require_author)]
AuthoringServiceDep = Annotated[AuthoringService, Depends(get_authoring_service)]


@router.post(
    "/questionnaire-drafts",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
    operation_id="createQuestionnaireDraft",
)
async def create_draft(
    body: CreateDraftRequest,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> Any:
    if not body.id.strip():
        raise validation_problem("'id' must be a non-empty string.")
    if not body.title.strip():
        raise validation_problem("'title' must be a non-empty string.")

    return await service.create_draft(
        draft_id=body.id.strip(),
        title=body.title.strip(),
        output_contract=body.output_contract,
        description=body.description,
    )


@router.get(
    "/questionnaire-drafts/{draft_id}",
    response_model=None,
    operation_id="getQuestionnaireDraft",
)
async def get_draft(
    draft_id: str,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> dict[str, Any]:
    result = await service.get_draft(draft_id)
    if result is None:
        raise not_found_problem(f"Draft '{draft_id}' not found.")
    return result


@router.patch(
    "/questionnaire-drafts/{draft_id}",
    response_model=None,
    operation_id="updateQuestionnaireDraft",
)
async def update_draft(
    draft_id: str,
    body: UpdateDraftRequest,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> Any:
    result = await service.update_draft(draft_id, operations=body.operations)
    if result is None:
        raise not_found_problem(f"Draft '{draft_id}' not found.")
    return result


@router.post(
    "/questionnaire-drafts/{draft_id}/decisions",
    response_model=None,
    operation_id="resolveAuthoringDecision",
)
async def resolve_decision(
    draft_id: str,
    body: ResolveDecisionRequest,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> Any:
    try:
        result = await service.resolve_decision(
            draft_id,
            decision_id=body.decision_id,
            action=body.action,
            resolution=body.resolution,
        )
    except ValueError as exc:
        raise validation_problem(str(exc)) from exc
    if result is None:
        raise not_found_problem(f"Draft '{draft_id}' not found.")
    return result


@router.put(
    "/questionnaire-drafts/{draft_id}/raw",
    response_model=None,
    operation_id="replaceQuestionnaireDraftRaw",
)
async def replace_raw_draft(
    draft_id: str,
    body: RawDraftRequest,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> Any:
    try:
        result = await service.replace_raw_draft(
            draft_id,
            title=body.title,
            description=body.description,
            output_contract=body.output_contract,
            questions=body.questions,
            decisions=[decision.model_dump(exclude_none=True) for decision in body.decisions],
            health_policy=body.health_policy,
            assistance_policy=body.assistance_policy,
        )
    except ValueError as exc:
        raise validation_problem(str(exc)) from exc
    if result is None:
        raise not_found_problem(f"Draft '{draft_id}' not found.")
    return result


@router.delete(
    "/questionnaire-drafts/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    operation_id="deleteQuestionnaireDraft",
)
async def delete_draft(
    draft_id: str,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> None:
    deleted = await service.delete_draft(draft_id)
    if not deleted:
        raise not_found_problem(f"Draft '{draft_id}' not found.")


@router.post(
    "/questionnaire-drafts/{draft_id}/publish",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
    operation_id="publishQuestionnaireDraft",
)
async def publish_draft(
    draft_id: str,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> dict[str, Any]:
    try:
        record = await service.publish_draft(draft_id, published_by=identity.actor_id)
    except ValueError as exc:
        raise validation_problem(str(exc)) from exc

    if record is None:
        raise not_found_problem(f"Draft '{draft_id}' not found.")

    return {
        "questionnaire_id": str(record.questionnaire_id),
        "version": record.version,
        "title": record.title,
        "content_hash": record.content_hash,
        "published_by": record.published_by,
        "published_at": record.published_at.isoformat(),
    }


@router.get(
    "/questionnaires/{questionnaire_id}/versions/{version}",
    response_model=None,
)
async def get_published_questionnaire(
    questionnaire_id: str,
    version: int,
    identity: AuthorDep,
    service: AuthoringServiceDep,
) -> dict[str, Any]:
    from qava.domain.models import QuestionnaireId

    result = await service._questionnaires.get(QuestionnaireId(questionnaire_id), version)
    if result is None:
        raise not_found_problem(
            f"Published questionnaire '{questionnaire_id}' version {version} not found."
        )
    return result.model_dump(mode="json")
