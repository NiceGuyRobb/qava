# API Contract: Deterministic Runtime Hardening

This document describes the public API changes and additions introduced by feature 002.
All existing `/api/v1` paths are preserved. Changes are additive or correctness-fixing.

## What Changes

| Area | Before | After |
|---|---|---|
| Router request parsing | `dict[str, Any]` with manual `.get()` | Typed `RequestModel` via Pydantic |
| Router response models | `response_model=None` | Explicit `response_model=ResponseType` |
| Operation IDs | FastAPI auto-generated | Explicit stable camelCase (matches current YAML) |
| Error responses | Ad-hoc inline dicts | Declared `ProblemDetail` response for 404/409/422 |
| Contract artifact location | `specs/001-qava-mvp/contracts/openapi.yaml` (manual) | `openapi/qava.openapi.json` (generated, committed) |
| Frontend generation source | Feature-001 YAML | Runtime-exported `openapi/qava.openapi.json` |
| Draft DELETE | No-op (read-then-204) | Real deletion via `AuthoringService.delete_draft` |
| Skip action | Always offered | Offered only when `"skip" in session_view.actions` |
| Navigate response | Focus not persisted or honored | Focus persisted; honored by evaluator until cleared |

## Session View Shape (extended, not breaking)

The `SessionView` response now derives all fields from one `SessionEvaluation`. The `actions`
field is truthful: `"skip"` appears only when the current interaction is optional and not already
skipped; `"navigate"` appears only when there are unresolved navigable needs.

```json
{
  "session": { "id": "...", "questionnaire_id": "...", "questionnaire_version": 1, "revision": 3, "status": "active" },
  "progress": { "satisfied_required": 1, "total_required": 3 },
  "current_interaction": {
    "id": "q-rooms",
    "kind": "question",
    "output_need_ids": ["need:rooms"],
    "prompt": "How many bedrooms?",
    "reason": "Collect evidence for the output contract.",
    "required": false,
    "answer_schema": { "type": "integer", "minimum": 1 },
    "component": { "name": "number_input", "version": 1, "props": {} }
  },
  "result": {
    "session_id": "...",
    "revision": 3,
    "status": "in_progress",
    "data": { "project": { "name": "North Star House" } },
    "provenance": { "/project/name": ["project-name"] },
    "unresolved_output_needs": [
      { "id": "need:rooms", "target": "/rooms", "label": "Rooms", "required": false, "criticality": "normal", "question_id": "q-rooms", "topic_id": "rooms" }
    ],
    "issues": []
  },
  "health": {
    "revision": 3,
    "score": 33,
    "readiness": "not_ready",
    "dimensions": { "completeness": 33, "validity": 100, "confidence": 100, "consistency": 100, "specificity": 100 },
    "attention": [],
    "calculation_version": 1
  },
  "actions": ["answer", "skip", "navigate", "save_and_exit", "delete"],
  "changed_paths": []
}
```

## Problem Detail (shared, declared at every error status)

```json
{
  "type": "https://qava.dev/problems/not-found",
  "title": "Not Found",
  "detail": "Draft 'my-qs' not found.",
  "status": 404
}
```

Applied to: 404 Not Found, 409 Conflict (stale revision), 422 Validation Problem.

## Stable Operation IDs

| Path | Method | Operation ID |
|---|---|---|
| `/questionnaire-drafts` | POST | `createQuestionnaireDraft` |
| `/questionnaire-drafts/{draftId}` | GET | `getQuestionnaireDraft` |
| `/questionnaire-drafts/{draftId}` | PATCH | `updateQuestionnaireDraft` |
| `/questionnaire-drafts/{draftId}` | DELETE | `deleteQuestionnaireDraft` |
| `/questionnaire-drafts/{draftId}/publish` | POST | `publishQuestionnaireDraft` |
| `/questionnaires/{questionnaireId}/versions/{version}` | GET | `getPublishedQuestionnaire` |
| `/sessions` | POST | `createSession` |
| `/sessions/{sessionId}` | GET | `getSession` |
| `/sessions/{sessionId}` | DELETE | `deleteSession` |
| `/sessions/{sessionId}/answers` | POST | `submitAnswer` |
| `/sessions/{sessionId}/skips` | POST | `skipInteraction` |
| `/sessions/{sessionId}/navigation` | POST | `navigate` |

## Contract Artifact Lifecycle

```
FastAPI routers (authoritative)
  -> create_app().openapi()
  -> qava openapi export --output openapi/qava.openapi.json
  -> committed to repository
  -> openapi-typescript openapi/qava.openapi.json -o frontend/src/api/generated/schema.ts
  -> frontend build and typecheck
```

Contract validation (`qava openapi validate`) fails CI if the committed artifact differs from
`create_app().openapi()` across paths, operations, request bodies, responses, or shared schemas.

## Equality Scope

The validation compares the complete exported JSON object after canonical serialization. Fields in scope:

- `openapi` version string
- `info` object (title, version, description)
- `paths` — all entries including methods, operation IDs, parameters, request bodies, and responses
- `components.schemas` — all entries referenced by any path
- `components.responses` — shared reusable response definitions
- `components.parameters` — shared reusable parameter definitions
- `security` and `components.securitySchemes`

Fields explicitly **not** excluded: required vs optional field changes, status codes, error schema
changes, and operation metadata. The comparison finds exactly those classes of drift.
