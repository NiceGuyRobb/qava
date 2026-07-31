from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from fastapi import Depends, HTTPException, Request, status

from qava.config import Settings, get_settings

RoleName = Literal["author", "respondent", "publisher"]
_ALLOWED_ROLES: frozenset[str] = frozenset({"author", "respondent", "publisher"})


@dataclass(frozen=True, slots=True)
class IdentityContext:
    actor_id: str
    roles: frozenset[RoleName]


def _forbidden(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "type": "https://qava.dev/problems/forbidden",
            "title": "Forbidden",
            "detail": message,
        },
    )


def parse_identity_header(raw_header: str) -> IdentityContext:
    try:
        payload = json.loads(raw_header)
    except json.JSONDecodeError as exc:
        raise _forbidden("Identity header must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise _forbidden("Identity header payload must be an object.")

    actor_id = payload.get("actor_id")
    roles = payload.get("roles")

    if not isinstance(actor_id, str) or not actor_id.strip():
        raise _forbidden("Identity payload must include a non-empty actor_id.")

    if not isinstance(roles, list) or not roles:
        raise _forbidden("Identity payload must include one or more roles.")

    normalized_roles: set[RoleName] = set()
    for role in roles:
        if not isinstance(role, str) or role not in _ALLOWED_ROLES:
            raise _forbidden("Identity payload includes an unsupported role.")
        normalized_roles.add(cast(RoleName, role))

    return IdentityContext(actor_id=actor_id.strip(), roles=frozenset(normalized_roles))


def get_identity(
    request: Request,
    settings: Settings = Depends(get_settings),  # noqa: B008 - FastAPI dependency injection
) -> IdentityContext:
    raw_header = request.headers.get(settings.trusted_identity_header)
    if raw_header is None:
        raise _forbidden("Missing trusted identity header.")

    return parse_identity_header(raw_header)


def assert_has_role(identity: IdentityContext, role: RoleName) -> None:
    if role not in identity.roles:
        raise _forbidden(f"Role '{role}' is required for this operation.")


def require_role(role: RoleName):
    def dependency(
        identity: IdentityContext = Depends(get_identity),  # noqa: B008 - FastAPI dependency injection
    ) -> IdentityContext:
        assert_has_role(identity, role)
        return identity

    return dependency


require_author = require_role("author")
require_respondent = require_role("respondent")
require_publisher = require_role("publisher")


# ---------------------------------------------------------------------------
# Database session manager (singleton for the application lifetime)
# ---------------------------------------------------------------------------

_db_manager: DatabaseSessionManager | None = None


def get_db_manager() -> DatabaseSessionManager:
    global _db_manager
    if _db_manager is None:
        from qava.infrastructure.database.session import DatabaseSessionManager

        _db_manager = DatabaseSessionManager()
    return _db_manager


def set_db_manager(manager: DatabaseSessionManager | None) -> None:
    """Override the singleton for tests that inject an in-memory manager."""
    global _db_manager
    _db_manager = manager


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------


async def get_authoring_service() -> AsyncIterator[AuthoringService]:
    from qava.application.authoring import AuthoringService
    from qava.infrastructure.database.repositories import (
        SQLiteDraftRepository,
        SQLitePublishedQuestionnaireRepository,
    )

    manager = get_db_manager()
    async with manager.session() as db_session:
        yield AuthoringService(
            draft_repo=SQLiteDraftRepository(db_session),
            questionnaire_repo=SQLitePublishedQuestionnaireRepository(db_session),
        )


async def get_interviewing_service() -> AsyncIterator[InterviewingService]:
    from qava.application.assistance import AssistanceService
    from qava.application.interviewing import InterviewingService
    from qava.infrastructure.assistance.fixture import FixtureAssistanceProvider
    from qava.infrastructure.database.repositories import (
        SQLiteAssistanceProposalRepository,
        SQLiteInteractionRepository,
        SQLitePublishedQuestionnaireRepository,
        SQLiteSessionRepository,
    )

    manager = get_db_manager()
    settings = get_settings()
    async with manager.session() as db_session:
        assistance = (
            AssistanceService(
                FixtureAssistanceProvider(),
                SQLiteAssistanceProposalRepository(db_session),
            )
            if settings.assistance_mode == "fixture"
            else None
        )
        yield InterviewingService(
            questionnaire_repo=SQLitePublishedQuestionnaireRepository(db_session),
            session_repo=SQLiteSessionRepository(db_session),
            interaction_repo=SQLiteInteractionRepository(db_session),
            assistance_service=assistance,
        )


async def get_publishing_service() -> AsyncIterator[PublishingService]:
    from qava.application.publishing import PublishingService
    from qava.infrastructure.database.repositories import (
        SQLitePublicationAttemptRepository,
        SQLitePublishedArtifactRepository,
        SQLitePublishedQuestionnaireRepository,
        SQLiteSessionRepository,
    )

    manager = get_db_manager()
    async with manager.session() as db_session:
        yield PublishingService(
            questionnaire_repo=SQLitePublishedQuestionnaireRepository(db_session),
            session_repo=SQLiteSessionRepository(db_session),
            attempts_repo=SQLitePublicationAttemptRepository(db_session),
            artifacts_repo=SQLitePublishedArtifactRepository(db_session),
        )


if TYPE_CHECKING:
    from qava.application.authoring import AuthoringService
    from qava.application.interviewing import InterviewingService
    from qava.application.publishing import PublishingService
    from qava.infrastructure.database.session import DatabaseSessionManager
