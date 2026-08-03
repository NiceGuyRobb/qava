"""Contract tests for the authoring decision and raw-draft endpoints (US4)."""

from __future__ import annotations

from qava.main import create_app


def test_authoring_decision_and_raw_operations_are_declared() -> None:
    paths = create_app().openapi()["paths"]
    decisions = paths["/api/v1/questionnaire-drafts/{draft_id}/decisions"]["post"]
    assert decisions["operationId"] == "resolveAuthoringDecision"
    request_ref = decisions["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref.endswith("/ResolveDecisionRequest")

    raw = paths["/api/v1/questionnaire-drafts/{draft_id}/raw"]["put"]
    assert raw["operationId"] == "replaceQuestionnaireDraftRaw"
    raw_ref = raw["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert raw_ref.endswith("/RawDraftRequest")


def test_authoring_decision_schemas_are_declared() -> None:
    schemas = create_app().openapi()["components"]["schemas"]

    resolution = schemas["ResolveDecisionRequest"]
    assert set(resolution["required"]) == {"decision_id", "action"}
    assert set(resolution["properties"]["action"]["enum"]) == {
        "confirm",
        "override",
        "reject",
    }

    raw = schemas["RawDraftRequest"]
    assert {"title", "output_contract", "questions", "decisions"} <= set(raw["properties"])
