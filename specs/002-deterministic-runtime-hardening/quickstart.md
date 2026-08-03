# Quickstart Validation Guide: Deterministic Runtime Hardening

This guide describes how to verify that the feature's end-to-end behavior is correct after
implementation. It assumes a clean checkout and a working local development environment.

## Prerequisites

- Python 3.12+, `uv` package manager
- Node.js 20+, `npm`
- Playwright Chromium: `npx playwright install chromium`

## Setup

```powershell
# From repository root
uv run --project backend alembic -c backend/alembic.ini upgrade head
npm --prefix frontend install
npm --prefix frontend run api:generate
```

## 1. Evaluate Session Correctness

**What to verify**: Projection, progress, health, actions, and current interaction are mutually
consistent after every mutation; inactive retained evidence is excluded from all fields.

```powershell
uv run --project backend pytest backend/tests/unit/ -k "evaluation" -v
```

**Expected**: All evaluator matrix tests pass. Active-answer filtering is proven across
projection, health, unresolved needs, and selection. Inactive answers do not appear in
`result.data`, do not count toward health, and do not satisfy output needs.

## 2. Skip Semantics

**What to verify**: Permitted skips advance revision once; prohibited skips advance zero times;
stale-revision skips are rejected; re-entry after applicability change is supported.

```powershell
uv run --project backend pytest backend/tests/integration/ -k "skip" -v
```

**Expected**:

- Skipping an optional question: `revision` increments, same question absent from next
  `current_interaction`, audit row present with `kind = "skip"`.
- Skipping a required question: returns 422, `revision` unchanged, no audit row.
- Skipping with stale revision: returns 409, `revision` unchanged.
- Skipping the same question after answering a question that made it inapplicable and then
  applicable again: permitted, produces a new skip at the current revision.

## 3. Navigation Semantics

**What to verify**: Valid navigation makes the target the current interaction and survives the
complete response evaluation; invalid and stale targets leave session state unchanged.

```powershell
uv run --project backend pytest backend/tests/integration/ -k "navigation" -v
```

**Expected**:

- Navigate to an unresolved applicable output need: `current_interaction.id` is a question
  serving that need; `revision` increments; navigation audit row present.
- Navigate to a resolved need: returns 422, `revision` unchanged.
- Navigate to an inapplicable target: returns 422, `revision` unchanged.
- Navigate with stale revision: returns 409, `revision` unchanged.
- Resume the session: navigation focus still active, same question current.

## 4. API Contract Equality

**What to verify**: The committed `openapi/qava.openapi.json` artifact matches the running
application's OpenAPI document exactly.

```powershell
uv run --project backend python -m qava openapi export --output openapi/qava.openapi.json
uv run --project backend pytest backend/tests/contract/test_openapi.py -v
```

**Expected**: `test_openapi_contract_equals_runtime` passes with zero diff. No path, operation,
schema, or error response differs between the committed artifact and runtime output.

## 5. Frontend Client Compatibility

**What to verify**: Generated TypeScript types remain valid; the frontend can build and typecheck
against the updated contract without questionnaire-specific changes.

```powershell
npm --prefix frontend run api:generate
npm --prefix frontend run typecheck
npm --prefix frontend run test
```

**Expected**: All commands exit 0. `schema.ts` reflects the new typed session actions and no
`any`-typed fields appear for previously unmodeled responses.

## 6. Draft Deletion

**What to verify**: DELETE returns 204 when a draft exists and 404 when it does not; no draft
record remains after deletion.

```powershell
uv run --project backend pytest backend/tests/integration/ -k "draft_deletion or delete_draft" -v
```

**Expected**:

- Delete an existing draft: returns 204; subsequent GET returns 404.
- Delete an unknown draft: returns 404.

## 7. Migration Correctness

**What to verify**: Clean initialization reaches `head`; repeated migration is idempotent; file
and in-memory databases produce equivalent schemas; legacy schema stamps correctly.

```powershell
uv run --project backend pytest backend/tests/contract/ -k "migration or schema" -v
```

**Expected**:

- Clean in-memory upgrade reaches revision `0002_session_disposition_focus`.
- Repeated upgrade produces no changes and exits cleanly.
- Introspected schema of a file database equals introspected schema of an in-memory database at
  the same head revision.
- A database with `0001_initial` tables but no `alembic_version` is stamped by `db reconcile`;
  a database with mismatched columns is refused.

## 8. End-to-End Regression

**What to verify**: The existing deterministic interview journey continues to pass across all
Playwright projects; backend suites have no required-workflow skips.

```powershell
# Start backend and frontend (separate terminals)
uv run --project backend uvicorn qava.main:app --host 127.0.0.1 --port 8000
npm run dev --prefix frontend -- --host 127.0.0.1

# Run E2E
npm --prefix frontend run test:e2e
```

**Expected**: Desktop, mobile, and reduced-motion Playwright projects pass. The respondent
answers, sees the canonical result update, and resumes the exact revision after reload. No test
skips due to unavailable authoring, session, skip, navigation, or deletion endpoints.

## Success Criteria Coverage

| SC | Validation step |
|---|---|
| SC-001 (consistent active evidence) | Step 1: evaluation matrix |
| SC-002 (skip revision/re-entry) | Step 2: skip integration |
| SC-003 (navigation selection/rejection) | Step 3: navigation integration |
| SC-004 (zero contract diff) | Step 4: contract equality |
| SC-005 (clean/repeated migration) | Step 7: migration tests |
| SC-006 (schema equality) | Step 7: migration tests |
| SC-007 (no availability skips) | Steps 2, 3, 6: no pytest.skip on endpoints |
| SC-008 (browser tests pass) | Step 8: Playwright |
| SC-009 (one authority per domain) | Steps 4, 7: single artifact and single migration chain |
