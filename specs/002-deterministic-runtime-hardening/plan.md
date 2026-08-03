# Implementation Plan: Deterministic Runtime Hardening

**Branch**: `002-deterministic-runtime-hardening` | **Date**: 2026-07-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-deterministic-runtime-hardening/spec.md`

## Summary

Harden the deterministic MVP without expanding its product surface. Extract one pure session
evaluation that derives active evidence, projection, unresolved needs, progress, health,
readiness, permitted actions, and next interaction from a published questionnaire and persisted
session state. Persist skip dispositions and navigation focus atomically with the existing session
revision, while interactions remain immutable audit evidence. Make typed FastAPI request and
response models the public API authority, export one generated OpenAPI review artifact for client
generation and exact equality checks, and make Alembic the only persistent-schema authority for
startup, tests, and local tooling. Complete the slice with actual draft deletion and focused
boundary tests that cannot skip required workflows.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.8; Vue 3.5

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, `aiosqlite`, Typer;
Vue 3, Pinia, Vue Router 4, Vite, `openapi-typescript`

**Storage**: SQLite in WAL mode; Alembic migration history is the sole schema authority; session
rows gain JSON state for skip dispositions and navigation focus while immutable interaction rows
retain audit evidence

**Testing**: pytest and HTTPX for unit, contract, migration, and full-stack integration tests;
Vitest and `vue-tsc` for generated-client compatibility; Playwright for the existing desktop,
mobile, and reduced-motion deterministic journey

**Target Platform**: Existing single-tenant Linux deployment; local Windows/macOS/Linux
development; evergreen desktop and mobile browsers

**Project Type**: Existing web application with a Python API/domain backend and Vue single-page
client; this feature changes backend ownership boundaries and generated client contracts only

**Performance Goals**: Preserve the MVP goal that at 100 active sessions at least 95% of accepted
mutations return a complete session view within 1 second and all complete within 3 seconds; one
evaluation performs bounded linear passes over the questionnaire and current answers

**Constraints**: Preserve public `/api/v1` URLs, accepted answer values, immutable questionnaire
versions, complete `SessionView` replacement, exact revision compare-and-swap, projection
provenance, five health dimensions, generic renderers, and explicit publication; no event store,
new adapter, assistance behavior, publication work, or questionnaire-specific client logic

**Scale/Scope**: One deterministic runtime, one public API contract authority, one migration
authority, two session-state additions, one corrected draft deletion path, and focused tests for
the existing single-tenant/100-session MVP boundary

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-research | Post-design evidence |
|---|---|---|
| Output contract | PASS | Applicability and active evidence are computed once, then used consistently for output-need satisfaction, projection, provenance, health, readiness, and selection. JSON Schema remains the output authority. |
| Simple runtime | PASS | The evaluator is a pure function of one published questionnaire and one session snapshot. Persisted dispositions and focus are compact inputs, not a graph, workflow language, or event-sourced runtime. |
| Typed UI | PASS | Existing answer schemas, stable machine values, and component specifications are preserved. The frontend continues replacing one generated `SessionView` and receives truthful action availability. |
| Bounded AI | PASS | No AI path is introduced or changed. All evaluation, action validation, contract generation, migration, and deletion behavior is deterministic. |
| Continuous projection | PASS | Every read and accepted answer, skip, or navigation mutation passes through the same evaluator and returns projection, provenance, health, readiness, actions, and next interaction together. |
| Explainable health | PASS | Existing published health policy and five dimensions remain intact; health consumes the evaluator's active evidence and retains evidence-linked attention. |
| Stable publication | PASS | Published questionnaires remain immutable and sessions remain revision-checked and resumable. Interaction rows retain actor/revision audit evidence; result publication is unchanged and out of scope. |

All gates pass before research and after Phase 1 design. No constitutional exception or
Complexity Tracking entry is required.

## Project Structure

### Documentation (this feature)

```text
specs/002-deterministic-runtime-hardening/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-contract.md
└── tasks.md                 # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
backend/
├── migrations/
│   └── versions/            # Immutable schema history; new additive session-state revision
├── src/qava/
│   ├── api/
│   │   ├── schemas.py       # Typed transport requests, responses, and problem details
│   │   └── routers/         # Stable operations with explicit models and operation IDs
│   ├── application/
│   │   ├── interviewing.py  # Revision-checked mutation orchestration only
│   │   └── authoring.py     # Adds real draft deletion use case
│   ├── domain/
│   │   ├── evaluation.py    # Pure complete session evaluation
│   │   ├── models.py        # Persisted session/disposition/focus records
│   │   ├── projection.py
│   │   ├── health.py
│   │   └── selection.py
│   ├── infrastructure/
│   │   └── database/
│   │       ├── migrate.py   # Programmatic Alembic upgrade/reconciliation entry point
│   │       ├── session.py   # Startup delegates to migration authority
│   │       └── repositories.py
│   └── cli.py               # OpenAPI export/validate and legacy DB reconciliation
└── tests/
    ├── unit/                # Evaluation and action-rule matrices
    ├── contract/            # Complete OpenAPI and schema-authority checks
    └── integration/         # Mutation, deletion, migration, and concurrency boundaries

frontend/
├── package.json             # Generate types from the runtime-exported OpenAPI artifact
├── src/api/generated/schema.ts
└── e2e/tests/deterministic-interview.spec.ts

openapi/
└── qava.openapi.json        # Generated review/client artifact; never hand-maintained
```

**Structure Decision**: Build directly on the 001 MVP's single backend and frontend. Add one pure
domain evaluation module because it removes competing rule interpretations; keep orchestration in
the existing application service and persistence in the existing repositories. Move the generated
OpenAPI artifact out of a historical feature directory into stable repository-level `openapi/` so
current runtime models, tests, and frontend generation share one derivation chain. Do not create a
new service, package workspace, schema DSL, event store, or frontend state model.

## Design Decisions

### One Complete Evaluation

`evaluate_session(questionnaire, session)` returns an immutable `SessionEvaluation`. It first
computes applicable question IDs and active answers. Every downstream calculation consumes those
same values: projection and provenance, unresolved needs, progress, health and readiness,
permitted actions, and deterministic selection. The returned current interaction honors a valid
navigation focus before ordinary ordering, and excludes answered or currently skipped questions.

Application mutations evaluate before writing to validate the requested action against current
state, perform one revision-checked update containing answers/dispositions/focus, append immutable
audit evidence in the same transaction, and evaluate the updated snapshot once for the response.
Reads use the identical response evaluation. A failed validation or stale compare-and-swap changes
neither session state nor audit evidence.

### Compact Authoritative Session State

Skip disposition and navigation focus belong in the session snapshot because they directly affect
the next deterministic evaluation. Interaction rows remain the audit log but are not replayed to
reconstruct current state. A skip disposition records question ID, actor, and accepted revision.
It suppresses the unchanged eligible question; if the question becomes inapplicable, evaluation
clears its effective suppression so a later transition back to applicable makes it eligible again.
Navigation focus records exactly one target question plus its output need or topic context and is
cleared when answered, skipped, resolved, or inapplicable.

### Runtime-Generated Public Contract

Pydantic transport models and explicit FastAPI route metadata are authoritative. Routers receive
typed request objects and declare success plus shared problem responses; application/domain
records remain separate and are converted at the boundary. Explicit operation IDs keep generated
client names stable. `qava openapi export` writes deterministic JSON to
`openapi/qava.openapi.json`; contract validation compares the complete normalized generated
document with that artifact and fails on added, removed, or changed paths, operations, request
bodies, responses, or shared schemas. The frontend generates types only from this artifact.

### Alembic-Only Schema Lifecycle

Alembic migrations are immutable and authoritative. A programmatic upgrade helper accepts an
existing SQLAlchemy connection so file databases and the shared in-memory integration database
run the same revisions without nested event loops or separate connections. Startup creates the
SQLite parent directory and applies runtime pragmas, then upgrades to `head`. Legacy databases
with application tables but no `alembic_version` are never stamped blindly: reconciliation first
compares their introspected schema with the expected 0001 shape, stamps only an exact match, and
otherwise fails with a diagnostic. The embedded `_SCHEMA_SQL` definition is removed.

## Delivery Slices

### Slice 1: Authoritative Session Evaluation (P1)

- Add typed session disposition/focus state and one additive Alembic revision.
- Extract the pure evaluator over existing condition, projection, health, and selection rules.
- Route create/read/answer responses through it and prove inactive retained evidence is excluded
  consistently from every derived field.
- Gate: evaluator matrix and existing answer/resume journey pass with no client-specific changes.

### Slice 2: Truthful Skip and Navigation (P1)

- Validate action permission against the pre-mutation evaluation.
- Persist accepted skip disposition or navigation focus in the same compare-and-swap as revision.
- Append actor/revision audit evidence only after the state update succeeds; clear state by the
  documented deterministic transitions.
- Gate: permitted/prohibited/stale skip and valid/invalid/stale navigation tests prove exact
  revision behavior, target selection, resume, and unchanged state on rejection.

### Slice 3: Runtime API Authority and Draft Deletion (P2)

- Introduce typed transport models and shared problem responses for every public route.
- Preserve URLs and explicit stable operation IDs; implement deletion through
  `AuthoringService.delete_draft` and the existing repository delete operation.
- Export the complete runtime OpenAPI document to the stable artifact, deep-compare it in contract
  tests, and regenerate frontend types from that artifact.
- Gate: zero OpenAPI diff, valid/invalid payload conformance, generated-client typecheck, and real
  existing/missing draft deletion pass without endpoint-availability skips.

### Slice 4: Alembic-Only Initialization (P3)

- Add the session-state migration and a connection-aware Alembic upgrade helper.
- Switch application, CLI, and integration fixtures to the helper; remove embedded schema SQL.
- Add verified legacy reconciliation plus clean/repeated/file/in-memory schema tests.
- Gate: clean and repeated upgrades reach `head`; file and test schemas are structurally equal;
  exact legacy schema stamps safely and mismatched legacy schema is refused.

### Slice 5: End-to-End Regression (P1)

- Run backend unit, contract, and integration suites with no required-workflow skips.
- Run frontend typecheck/unit tests and the existing Playwright desktop, mobile, and reduced-motion
  projects against the regenerated contract.
- Gate: all SC-001 through SC-009 evidence passes and the three constitution authorities remain
  singular in code and tests.

## Task Generation Guardrails

- Generate tasks in slice order and keep the deterministic interview runnable after each slice.
- Every task names an exact file path and observable test; do not create a generic refactoring phase.
- Add the session-state migration as a new revision; never rewrite `0001_initial` after release.
- Keep `evaluate_session` pure and framework-independent. Reuse condition, projection, health, and
  selection functions, adjusting them only where active-evidence inputs require one shared rule.
- Mutation orchestration owns transactions and compare-and-swap; domain evaluation performs no I/O.
- Do not derive authoritative state by replaying interaction history. State is the snapshot;
  interactions are audit evidence.
- Do not hand-edit generated OpenAPI or frontend schema files. Generate them from typed runtime
  models and fail validation on drift.
- Required endpoint tests must fail, never skip, when authoring, publication, session, skip,
  navigation, or deletion operations are unavailable.
- Python tasks load `fastapi-python` and `python-best-practices`; frontend changes load
  `vue-best-practices`, and routing changes additionally load `vue-router-best-practices`.
- Preserve unrelated deferred MVP surfaces: assistance, result publication, self-hosted authoring,
  adapters, and broad UI work remain out of scope.

## Complexity Tracking

No violations. The only new domain abstraction replaces several competing calculations with one
pure result. The only persistence additions are compact state required for deterministic resume;
the existing interaction table remains audit-only, and no new subsystem is introduced.
