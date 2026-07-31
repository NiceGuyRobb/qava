from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from qava.api.dependencies import (
    IdentityContext,
    assert_has_role,
    get_identity,
    parse_identity_header,
    require_role,
)
from qava.config import Settings


def _request_with_header(header_name: str, header_value: str) -> Request:
    scope = {
        "type": "http",
        "headers": [(header_name.lower().encode("utf-8"), header_value.encode("utf-8"))],
    }
    return Request(scope)


def test_parse_identity_header_accepts_valid_roles() -> None:
    identity = parse_identity_header(
        json.dumps({"actor_id": "user-1", "roles": ["author", "respondent"]})
    )

    assert identity.actor_id == "user-1"
    assert identity.roles == frozenset({"author", "respondent"})


@pytest.mark.parametrize(
    "payload",
    [
        "not-json",
        "[]",
        json.dumps({"actor_id": "", "roles": ["author"]}),
        json.dumps({"actor_id": "user-1", "roles": []}),
        json.dumps({"actor_id": "user-1", "roles": ["owner"]}),
    ],
)
def test_parse_identity_header_rejects_invalid_payloads(payload: str) -> None:
    with pytest.raises(HTTPException) as exc:
        parse_identity_header(payload)

    assert exc.value.status_code == 403


def test_get_identity_uses_trusted_header_name() -> None:
    settings = Settings(trusted_identity_header="X-Qava-Identity")
    request = _request_with_header(
        "X-Qava-Identity",
        json.dumps({"actor_id": "user-7", "roles": ["publisher"]}),
    )

    identity = get_identity(request=request, settings=settings)

    assert identity == IdentityContext(actor_id="user-7", roles=frozenset({"publisher"}))


def test_get_identity_rejects_missing_header() -> None:
    settings = Settings(trusted_identity_header="X-Qava-Identity")
    request = Request({"type": "http", "headers": []})

    with pytest.raises(HTTPException) as exc:
        get_identity(request=request, settings=settings)

    assert exc.value.status_code == 403


def test_role_assertion_rejects_missing_role() -> None:
    identity = IdentityContext(actor_id="user-2", roles=frozenset({"respondent"}))

    with pytest.raises(HTTPException) as exc:
        assert_has_role(identity, "author")

    assert exc.value.status_code == 403


def test_role_dependency_allows_matching_role() -> None:
    identity = IdentityContext(actor_id="user-3", roles=frozenset({"author"}))
    dependency = require_role("author")

    assert dependency(identity=identity) == identity
