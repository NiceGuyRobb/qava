"""Sessions API router: create, get, answer, skip, navigate, delete."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from qava.api.dependencies import (
    IdentityContext,
    get_interviewing_service,
    get_publishing_service,
    require_publisher,
    require_respondent,
)
from qava.api.errors import conflict_problem, not_found_problem, validation_problem
from qava.api.schemas import (
    CreateSessionRequest,
    NavigateRequest,
    PublicationList,
    PublicationReceipt,
    PublishRequest,
    ResultPreview,
    SessionView,
    SkipInteractionRequest,
    SubmitAnswerRequest,
)
from qava.application.interviewing import InterviewingService, StaleRevisionError
from qava.application.publishing import (
    NotReadyError,
    PublicationNotFoundError,
    PublishingService,
    SessionNotFoundError,
)
from qava.application.publishing import StaleRevisionError as PublishStaleRevisionError
from qava.domain.models import PublicationRecord

router = APIRouter(prefix="/api/v1", tags=["sessions"])

RespondentDep = Annotated[IdentityContext, Depends(require_respondent)]
PublisherDep = Annotated[IdentityContext, Depends(require_publisher)]
InterviewingServiceDep = Annotated[InterviewingService, Depends(get_interviewing_service)]
PublishingServiceDep = Annotated[PublishingService, Depends(get_publishing_service)]


def _receipt(record: PublicationRecord) -> PublicationReceipt:
    return PublicationReceipt(
        publication_id=str(record.publication_id),
        session_id=str(record.session_id),
        session_revision=record.session_revision,
        adapter=record.adapter,
        destination=record.destination,
        idempotency_key=record.idempotency_key,
        status=record.status,
        requested_by=record.requested_by,
        external_reference=record.external_reference,
        error=(None if record.error is None else record.error.model_dump(exclude_none=True)),
    )


@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionView,
    operation_id="createSession",
)
async def create_session(
    body: CreateSessionRequest,
    identity: RespondentDep,
    service: InterviewingServiceDep,
) -> Any:
    result = await service.create_session(
        questionnaire_id=body.questionnaire_id,
        questionnaire_version=body.questionnaire_version,
        created_by=identity.actor_id,
    )
    if result is None:
        raise not_found_problem(
            f"Questionnaire '{body.questionnaire_id}' version {body.questionnaire_version} not found."
        )
    return result


@router.get(
    "/sessions/{session_id}",
    response_model=SessionView,
    operation_id="getSession",
)
async def get_session(
    session_id: str,
    identity: RespondentDep,
    service: InterviewingServiceDep,
) -> Any:
    result = await service.get_session(session_id)
    if result is None:
        raise not_found_problem(f"Session '{session_id}' not found.")
    return result


@router.post(
    "/sessions/{session_id}/answers",
    response_model=SessionView,
    operation_id="submitAnswer",
)
async def submit_answer(
    session_id: str,
    body: SubmitAnswerRequest,
    identity: RespondentDep,
    service: InterviewingServiceDep,
) -> Any:
    try:
        result = await service.submit_answer(
            session_id,
            question_id=body.interaction_id,
            value=body.value,
            expected_revision=body.expected_revision,
            actor_id=identity.actor_id,
        )
    except KeyError as exc:
        raise not_found_problem(f"Not found: {exc}") from exc
    except StaleRevisionError as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://qava.dev/problems/stale-revision",
                "title": "Stale Revision",
                "detail": str(exc),
                "status": 409,
            },
        ) from exc
    except ValueError as exc:
        raise validation_problem(str(exc)) from exc
    return result


@router.post(
    "/sessions/{session_id}/skips",
    response_model=SessionView,
    operation_id="skipInteraction",
)
async def skip_interaction(
    session_id: str,
    body: SkipInteractionRequest,
    identity: RespondentDep,
    service: InterviewingServiceDep,
) -> Any:
    try:
        result = await service.skip_interaction(
            session_id,
            question_id=body.interaction_id,
            expected_revision=body.expected_revision,
            actor_id=identity.actor_id,
        )
    except KeyError as exc:
        raise not_found_problem(f"Not found: {exc}") from exc
    except StaleRevisionError as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://qava.dev/problems/stale-revision",
                "title": "Stale Revision",
                "detail": str(exc),
                "status": 409,
            },
        ) from exc
    except ValueError as exc:
        raise validation_problem(str(exc)) from exc
    return result


@router.post(
    "/sessions/{session_id}/navigation",
    response_model=SessionView,
    operation_id="navigate",
)
async def navigate(
    session_id: str,
    body: NavigateRequest,
    identity: RespondentDep,
    service: InterviewingServiceDep,
) -> Any:
    if (body.section_id is None) == (body.output_need_id is None):
        raise validation_problem("Provide exactly one of 'section_id' or 'output_need_id'.")

    try:
        result = await service.navigate(
            session_id,
            section_id=body.section_id,
            output_need_id=body.output_need_id,
            expected_revision=body.expected_revision,
            actor_id=identity.actor_id,
        )
    except KeyError as exc:
        raise not_found_problem(f"Not found: {exc}") from exc
    except StaleRevisionError as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://qava.dev/problems/stale-revision",
                "title": "Stale Revision",
                "detail": str(exc),
                "status": 409,
            },
        ) from exc
    except ValueError as exc:
        raise validation_problem(str(exc)) from exc
    return result


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    operation_id="deleteSession",
)
async def delete_session(
    session_id: str,
    identity: RespondentDep,
    service: InterviewingServiceDep,
) -> None:
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise not_found_problem(f"Session '{session_id}' not found.")


@router.get(
    "/sessions/{session_id}/result/preview",
    response_model=ResultPreview,
    operation_id="previewResult",
)
async def preview_result(
    session_id: str,
    identity: PublisherDep,
    service: PublishingServiceDep,
) -> Any:
    try:
        return await service.preview(session_id)
    except SessionNotFoundError as exc:
        raise not_found_problem(f"Session '{session_id}' not found.") from exc
    except NotReadyError as exc:
        raise validation_problem(str(exc)) from exc


@router.post(
    "/sessions/{session_id}/publications",
    status_code=status.HTTP_201_CREATED,
    response_model=PublicationReceipt,
    operation_id="publishResult",
)
async def publish_result(
    session_id: str,
    body: PublishRequest,
    identity: PublisherDep,
    service: PublishingServiceDep,
) -> Any:
    try:
        record = await service.publish(
            session_id,
            idempotency_key=body.idempotency_key,
            expected_revision=body.expected_revision,
            requested_by=identity.actor_id,
            adapter_name=body.adapter,
        )
    except SessionNotFoundError as exc:
        raise not_found_problem(f"Session '{session_id}' not found.") from exc
    except PublishStaleRevisionError as exc:
        raise conflict_problem(str(exc)) from exc
    except NotReadyError as exc:
        raise validation_problem(str(exc)) from exc
    return _receipt(record)


@router.get(
    "/sessions/{session_id}/publications",
    response_model=PublicationList,
    operation_id="listPublications",
)
async def list_publications(
    session_id: str,
    identity: PublisherDep,
    service: PublishingServiceDep,
) -> Any:
    records = await service.list_publications(session_id)
    return PublicationList(publications=[_receipt(record) for record in records])


@router.post(
    "/sessions/{session_id}/publications/{publication_id}/reconcile",
    response_model=PublicationReceipt,
    operation_id="reconcilePublication",
)
async def reconcile_publication(
    session_id: str,
    publication_id: str,
    identity: PublisherDep,
    service: PublishingServiceDep,
) -> Any:
    try:
        record = await service.reconcile(
            session_id,
            publication_id,
            requested_by=identity.actor_id,
        )
    except PublicationNotFoundError as exc:
        raise not_found_problem(
            f"Publication '{publication_id}' not found for session '{session_id}'."
        ) from exc
    return _receipt(record)
