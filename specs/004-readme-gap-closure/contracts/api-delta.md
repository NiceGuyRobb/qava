# API Delta: README Gap Closure

New and changed HTTP operations only. All paths are under the existing `/api/v1` base and return the standard complete session view (or a receipt) using existing shapes unless noted. Errors use RFC 7807 `application/problem+json`.

## New

### Preview a result (US2)

```http
GET /api/v1/sessions/{session_id}/result/preview?revision={n}
```

- Side-effect free. Returns the canonical projection, health, attention, and provenance for the requested (or current) revision.
- 409 if `revision` is unknown.

### Publish a result (US2)

```http
POST /api/v1/sessions/{session_id}/publications
```

```json
{
  "expected_revision": 12,
  "adapter": "json_document",
  "idempotency_key": "b1e2..."
}
```

- Validates the publication gate, invokes the adapter, records and returns a receipt.
- **201** with the prior receipt when `idempotency_key` was already used (no duplicate artifact).
- **409** when `expected_revision` is stale.
- **422** when the gate fails, with blocking reasons in the problem detail.

Receipt shape:

```json
{
  "publication_id": "pub-1",
  "session_id": "session-1",
  "session_revision": 12,
  "adapter": "json_document",
  "destination": "qava-store://sessions/session-1/artifact",
  "idempotency_key": "b1e2...",
  "status": "succeeded",
  "requested_by": "publisher-1",
  "external_reference": "pub-1",
  "error": null
}
```

### List publications (US2, optional read)

```http
GET /api/v1/sessions/{session_id}/publications
```

- Returns prior attempts/receipts for audit.

### Reconcile an indeterminate publication (US2)

```http
POST /api/v1/sessions/{session_id}/publications/{publication_id}/reconcile
```

- Resolves a receipt in `outcome_unknown` to a terminal status (`succeeded`/`failed`) by re-checking the adapter, without creating a duplicate artifact.
- **200** with the updated receipt; **409** if the receipt is already terminal.

## Changed

### Draft authoring decisions (US4)

```http
GET   /api/v1/questionnaire-drafts/{draft_id}   # now includes pending decisions[]
POST  /api/v1/questionnaire-drafts/{draft_id}/decisions
```

```json
{ "decision_id": "d1", "action": "confirm | override | reject", "resolution": { "component": "money_input" } }
```

- Publishing a draft with any `pending` blocking decision returns **422**.

### Raw JSON authoring path (US4)

```http
PUT /api/v1/questionnaire-drafts/{draft_id}/raw
```

- Accepts a full questionnaire JSON body; passes the identical publication gate as the guided (meta-questionnaire) path. Cross-document reference issues return as validation attention, not hard parse errors.

### Registry adapter publication (US5)

- Uses the same `POST /sessions/{session_id}/publications` operation with `"adapter": "registry"`. The receipt's `external_reference` is `questionnaire:{id}@{version}`.

## Unchanged but relevant

- `POST /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/answers`, `POST /sessions/{id}/skips`, `POST /sessions/{id}/navigation` are unchanged; US1 (dynamic options, collections, money/date) is expressed entirely within the existing session view and answer contracts.
- US6 assistance has no new public endpoint; fixture proposals are applied inside existing evaluation/authoring flows and surfaced only through existing view fields plus audit records.

> The running app's generated OpenAPI remains the authoritative contract; this delta is a design summary and must match `openapi/qava.openapi.json` after implementation.
