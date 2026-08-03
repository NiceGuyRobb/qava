# Implementation Plan: Qava MVP

**Branch**: `001-qava-mvp` | **Date**: 2026-07-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-qava-mvp/spec.md`

## Summary

Build Qava as one contract-first web application: a Python engine compiles JSON Schema output
contracts into immutable questionnaires, FastAPI exposes deterministic authoring and interview
operations, and a Vue 3 client renders semantic answer components while keeping the full canonical
result and explainable health visible. SQLite persists the single-tenant MVP with revision-based
concurrency. Bounded assistance is a narrow optional provider behind validated structured output;
the deterministic engine remains complete without it. The Qava Cirrus design skill governs a
light, futuristic-functional interface and restrained question transitions.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.x; Vue 3.5

**Primary Dependencies**: FastAPI, Pydantic v2, `jsonschema`, `referencing`, SQLAlchemy 2 async,
Alembic, `aiosqlite`; Vue 3, Vite, Vue Router 4, Pinia, Lucide Vue Next

**Storage**: SQLite in WAL mode for drafts, immutable questionnaires, sessions, interactions,
assistance proposals, and publication attempts; approved filesystem directory for immutable JSON
document artifacts

**Testing**: pytest, pytest-asyncio, HTTPX, Hypothesis; Vitest, Vue Test Utils, `vue-tsc`;
Playwright for end-to-end, accessibility, responsive, reduced-motion, and visual checks; concurrent
HTTP acceptance test for 100 active sessions

**Target Platform**: Single-tenant Linux container; evergreen desktop and mobile browsers; local
Windows/macOS/Linux development

**Project Type**: Web application with Python API/engine and Vue single-page client, packaged as
one production deployable

**Performance Goals**: At 100 active sessions, at least 95% of accepted answer/edit requests
return a complete session view within 1 second and all complete within 3 seconds; question motion
maintains smooth transform/opacity rendering and never delays request completion

**Constraints**: One SQLite-writing application worker; host-provided identity with Qava role
checks; exact revision compare-and-swap; explicit idempotent publication; full deterministic
fallback; immutable questionnaire versions; collection depth 3, 100 items per collection, 2
clarification follow-ups, and 1,000 interactions per session

**Scale/Scope**: One tenant, 100 concurrently active interview sessions, one built-in web component
catalog, JSON document and questionnaire-registry adapters only, four user stories in one MVP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-research | Post-design evidence |
|---|---|---|
| Output contract | PASS | JSON Schema remains authoritative; `OutputNeed`, `Question`, `Mapping`, publication validation, and `ResultProjection` trace values to JSON Pointers. |
| Simple runtime | PASS | Pure engine services compute eligible interaction + projection + health from one published questionnaire and one session snapshot. No workflow graph or event-sourcing runtime is introduced. |
| Typed UI | PASS | The component catalog maps schema-compatible `ComponentSpec` values to focused Vue renderers. Renderers emit answers only; server services own mapping and selection. |
| Bounded AI | PASS | `AssistanceProvider` receives an already bounded operation and returns schema-validated proposals. Disabled/fixture providers and deterministic candidate order are complete fallbacks. |
| Continuous projection | PASS | Every accepted mutation transaction recomputes applicability, projection, provenance, health, readiness, and next candidates, then returns one `SessionView`. |
| Explainable health | PASS | Published `HealthPolicy` calculates five dimensions and evidence-linked attention; blocking issues remain explicit and headline score cannot publish alone. |
| Stable publication | PASS | Drafts are mutable; published questionnaire rows and publication attempts are immutable. Sessions pin exact versions and interactions retain runtime evidence. |

All gates pass. Re-check outcome after Phase 1 design: **PASS**. No constitutional exception or
Complexity Tracking entry is required.

## Project Structure

### Documentation (this feature)

```text
specs/001-qava-mvp/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── openapi.yaml     # Phase 1 API contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
backend/
├── pyproject.toml
├── alembic.ini
├── migrations/
├── src/qava/
│   ├── api/
│   │   ├── dependencies.py       # Identity, roles, repositories
│   │   ├── errors.py             # Problem details
│   │   └── routers/              # Drafts, questionnaires, sessions, publications
│   ├── application/
│   │   ├── authoring.py          # Draft compilation and publication use cases
│   │   ├── assistance.py         # Bounded proposals and deterministic fallback
│   │   ├── interviewing.py       # Session, answer, skip, navigation use cases
│   │   ├── options.py            # Named runtime option lookup
│   │   └── publishing.py         # Preview, idempotent publication, deletion
│   ├── domain/
│   │   ├── answers.py            # Typed answer validation
│   │   ├── models.py             # Typed immutable domain records
│   │   ├── definition.py         # Output needs and publication validation
│   │   ├── conditions.py         # equals/contains/exists
│   │   ├── components.py         # Catalog compatibility and inference
│   │   ├── projection.py         # Direct/compose mapping and provenance
│   │   ├── health.py             # Five dimensions and readiness
│   │   └── selection.py          # Eligibility and deterministic order
│   ├── ports/
│   │   ├── assistance.py         # Narrow typed assistance protocol
│   │   ├── repositories.py       # Draft/session/publication protocols
│   │   └── output_adapter.py     # validate/preview/publish protocol
│   ├── infrastructure/
│   │   ├── database/             # SQLAlchemy models and repositories
│   │   ├── assistance/           # Disabled, fixture, configured provider
│   │   ├── adapters/             # JSON document and registry adapters
│   │   └── contracts/            # Local JSON Schema registry/loader
│   ├── config.py
│   └── main.py
└── tests/
    ├── unit/
    ├── contract/
    ├── integration/
    └── performance/

frontend/
├── package.json
├── vite.config.ts
├── src/
│   ├── api/                       # Generated client plus thin error adapter
│   ├── assets/                    # Qava Cirrus tokens, fonts, atmosphere
│   ├── components/
│   │   ├── authoring/             # Draft decisions and validation
│   │   ├── interview/             # Question surface and navigation
│   │   ├── renderers/             # Semantic typed answer controls
│   │   ├── result/                # Tree/raw preview and provenance
│   │   ├── health/                # Dimensions and attention
│   │   └── publication/           # Exact-revision review and receipt
│   ├── composables/               # Focused route/data/motion behavior
│   ├── router/                    # Routes, role metadata, param lifecycle
│   ├── stores/                    # Identity and authoritative session/draft state
│   ├── views/                     # Thin composition surfaces
│   ├── App.vue
│   └── main.ts
└── tests/
    ├── unit/
    └── component/

e2e/
├── fixtures/
└── tests/                         # Playwright workflows and visual checks

data/
├── contracts/v1/                  # Engine-owned schemas updated to ratified model
├── components/catalog.v1.json     # Semantic client/server handshake
├── definitions/                   # Versioned authoring fixtures
└── examples/                      # Contract fixtures, never runtime data
```

**Structure Decision**: Keep one backend application and one frontend application. The backend's
domain layer is pure and framework-independent; application services coordinate the three required
ports. Vue route views compose focused feature components, while renderers implement only the
component catalog. Do not add shared-package workspaces, service boundaries, generic plugin
systems, or deployment orchestration for the MVP.

## Component Map

| Vue component/composable | Single responsibility | Contract |
|---|---|---|
| `InterviewView.vue` | Compose the active interview, preview, and health surfaces | Reads route ID; delegates state to `useSession` |
| `QuestionStage.vue` | Transition between one active interaction at a time | Props: interaction, pending; emits: answer, skip |
| `SemanticRenderer.vue` | Resolve a catalog name or explicit fallback | Props: component spec, answer schema, draft value; emits typed update/submit |
| `renderers/*.vue` | Capture one answer-shape family accessibly | Props down; emits machine value only |
| `ResultWorkspace.vue` | Compose tree/raw result modes and preview actions | Props: result, changed paths, provenance |
| `JsonTree.vue` | Render full navigable output tree | Props: JSON value, pointer, changed paths; emits pointer selection |
| `HealthPanel.vue` | Render five dimensions and evidence-linked attention | Props: health; emits attention selection |
| `SessionRail.vue` | Show global requirement progress, active topic, revision, readiness, and unresolved-need navigation | Props: session summary, progress, health, unresolved needs |
| `PublicationReview.vue` | Preview and explicitly publish an exact revision | Props: preview/receipt; emits preview/publish |
| `AuthoringView.vue` | Compose draft decisions, preview, and publication gate | Delegates state to `useDraft` |
| `DraftDecisionList.vue` | Resolve pending authoring decisions | Props: decisions; emits accept/reject/override |
| `useSession.ts` | Fetch and replace authoritative complete session views | Readonly state plus answer/skip/navigate/delete actions |
| `useDraft.ts` | Fetch and replace authoritative draft state | Readonly state plus explicit draft operations |
| `useQuestionMotion.ts` | Direction and reduced-motion transition state | No server/business decisions |

## API and Ownership Rules

1. FastAPI routers parse requests, enforce dependencies, invoke one application use case, and map
   domain errors to problem details. They contain no projection, health, or selection logic.
2. Application services own transactions. One accepted mutation creates interaction evidence,
   updates the session revision, derives the complete view, and commits atomically.
3. Domain services are pure functions over typed inputs. They import no FastAPI, SQLAlchemy,
   provider SDK, or definition pack.
4. Infrastructure implements only the three required port families: repositories, assistance,
   and output adapters.
5. The frontend never derives output mappings, requirement satisfaction, health, readiness, or the
   next interaction. It replaces local authoritative state with each complete server response.
6. OpenAPI is the frontend transport source. Generated files are not hand-edited.
7. The complete session view includes unresolved-need summaries and resolved component specs;
  separate catalog and unresolved-needs endpoints are intentionally unnecessary.

## Delivery Slices

### Slice 0: Contract and Skeleton

- Align seed v1 schemas, examples, and component catalog with the ratified specification.
- Scaffold backend/frontend tooling, database migration, OpenAPI validation, generated client, and
  Qava Cirrus global tokens.
- Gate: schemas/examples validate; backend and frontend type checks pass; backend startup and the
  frontend shell prove local setup.

### Slice 1: Deterministic Contract-to-Live-Result Loop (P1)

- Compile one output contract deterministically into output needs and questions.
- Validate and publish one immutable questionnaire.
- Start/resume a session, render catalog controls, accept/edit typed answers, evaluate conditions,
  map direct/compose values, return full projection/provenance, select deterministic next question,
  and reject stale revisions.
- Build the desktop split and mobile tabs with full output preview and keyed question transitions.
- Gate: custom-home fixture completes end to end with AI disabled; every accepted answer updates
  the visible canonical result and survives resume.

### Slice 2: Draft Authoring and Catalog Breadth (P1/P4 foundation)

- Add author decision resolution and compatible component override.
- Implement remaining required renderer families, collections, dynamic option providers, raw JSON
  authoring escape hatch, and publication validation issues.
- Gate: representative scalar, enum, conditional, collection, and dynamic-option contract publishes
  without questionnaire-specific Vue code.

### Slice 3: Bounded Assistance (P2)

- Add fixture provider first, structured proposal persistence, bounded ranking/clarification, policy
  enforcement, timeout/invalid-output fallback, and audit metadata.
- Gate: identical questionnaire completes with valid, unavailable, malformed, and prohibited
  assistance; only ordering/clarification differs.

### Slice 4: Health and Explicit Publication (P3)

- Implement five inspectable dimensions, attention evidence, readiness gates, side-effect-free
  preview, JSON document adapter, idempotency, receipts, role enforcement, and local-only deletion.
- Gate: incomplete -> attention -> ready -> published lifecycle is explainable; duplicate publish
  creates no second artifact; deletion leaves artifacts intact.

### Slice 5: Self-Hosted Authoring (P4)

- Publish the questionnaire schema as the meta output contract, bootstrap a meta-questionnaire,
  connect live component-catalog options, and publish through the registry adapter.
- Gate: create, validate, publish, and run a representative five-question questionnaire in 15
  minutes or less using Qava itself.

### Slice 6: Acceptance and Hardening

- Run contract, integration, accessibility, responsive, reduced-motion, visual, concurrency, and
  full-loop acceptance suites; validate quickstart from a clean checkout.
- Gate: all SC-001 through SC-014 evidence is recorded and constitution checks remain passing.

## Task Generation Guardrails

- Generate tasks in the slice order above. Do not create a generic infrastructure phase beyond the
  concrete prerequisites in Slice 0.
- Every implementation task names an exact file path and one observable outcome.
- Every affected contract, mapping, component compatibility, projection, health, concurrency,
  publication, or immutable-version boundary gets a paired automated test task.
- Prefer vertical tasks that complete one request-to-view path over batches of disconnected models.
- Create no adapter except JSON document and questionnaire registry; no provider framework beyond
  the one protocol and required implementations; no shared UI kit beyond tokens and components
  used by an MVP screen.
- Use the existing custom-home definition as the primary end-to-end fixture. Add a fixture only
  when it covers a shape not present there.
- UI tasks MUST load `vue-best-practices`, `vue-router-best-practices` when routing is touched, and
  `qava-cirrus-design`. Python tasks MUST load `fastapi-python` and `python-best-practices`.
- Complete and validate each slice before starting the next. The deterministic loop is always kept
  runnable.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. The design uses one backend, one frontend, one database, three requirement-driven
port families, and two output adapters required by the MVP.
