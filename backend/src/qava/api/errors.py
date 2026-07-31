from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from qava.domain.models import ProblemDetail


def _raise_problem(
    *,
    code: str,
    title: str,
    detail: str,
    status_code: int,
    instance: str | None = None,
    extra: dict[str, Any] | None = None,
) -> HTTPException:
    payload = ProblemDetail(
        type=f"https://qava.dev/problems/{code}",
        title=title,
        detail=detail,
        status=status_code,
        instance=instance,
    ).model_dump(exclude_none=True)

    if extra:
        payload.update(extra)

    return HTTPException(status_code=status_code, detail=payload)


def validation_problem(detail: str, *, instance: str | None = None) -> HTTPException:
    return _raise_problem(
        code="validation",
        title="Validation Failed",
        detail=detail,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        instance=instance,
    )


def forbidden_problem(detail: str, *, instance: str | None = None) -> HTTPException:
    return _raise_problem(
        code="forbidden",
        title="Forbidden",
        detail=detail,
        status_code=status.HTTP_403_FORBIDDEN,
        instance=instance,
    )


def not_found_problem(detail: str, *, instance: str | None = None) -> HTTPException:
    return _raise_problem(
        code="not-found",
        title="Not Found",
        detail=detail,
        status_code=status.HTTP_404_NOT_FOUND,
        instance=instance,
    )


def precondition_problem(detail: str, *, instance: str | None = None) -> HTTPException:
    return _raise_problem(
        code="precondition",
        title="Precondition Required",
        detail=detail,
        status_code=status.HTTP_428_PRECONDITION_REQUIRED,
        instance=instance,
    )


def conflict_problem(detail: str, *, instance: str | None = None) -> HTTPException:
    return _raise_problem(
        code="conflict",
        title="Conflict",
        detail=detail,
        status_code=status.HTTP_409_CONFLICT,
        instance=instance,
    )
