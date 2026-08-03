"""Contract tests for the publication endpoints (US2)."""

from __future__ import annotations

from qava.main import create_app


def _openapi() -> dict:
    return create_app().openapi()


def test_publication_operations_are_declared() -> None:
    spec = _openapi()
    paths = spec["paths"]

    preview = paths["/api/v1/sessions/{session_id}/result/preview"]["get"]
    assert preview["operationId"] == "previewResult"
    preview_ref = preview["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert preview_ref.endswith("/ResultPreview")

    publish = paths["/api/v1/sessions/{session_id}/publications"]["post"]
    assert publish["operationId"] == "publishResult"
    request_ref = publish["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref.endswith("/PublishRequest")
    publish_ref = publish["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    assert publish_ref.endswith("/PublicationReceipt")

    listing = paths["/api/v1/sessions/{session_id}/publications"]["get"]
    assert listing["operationId"] == "listPublications"
    list_ref = listing["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert list_ref.endswith("/PublicationList")

    reconcile = paths[
        "/api/v1/sessions/{session_id}/publications/{publication_id}/reconcile"
    ]["post"]
    assert reconcile["operationId"] == "reconcilePublication"


def test_publication_schemas_are_present() -> None:
    schemas = _openapi()["components"]["schemas"]

    assert set(schemas["PublishRequest"]["required"]) == {"idempotency_key", "expected_revision"}

    preview = schemas["ResultPreview"]["properties"]
    assert {"session_id", "revision", "adapter", "destination", "content_hash", "document"} <= set(
        preview
    )

    receipt = schemas["PublicationReceipt"]["properties"]
    assert {
        "publication_id",
        "session_id",
        "status",
        "adapter",
        "destination",
        "idempotency_key",
        "external_reference",
    } <= set(receipt)

    assert schemas["PublicationList"]["properties"]["publications"]["type"] == "array"
