# Tasks: README Gap Closure

**Input**: Design documents from `/specs/004-readme-gap-closure/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api-delta.md](contracts/api-delta.md), [quickstart.md](quickstart.md)

**Tests**: Constitution-required boundary tests (contract, mapping, component compatibility, projection, health, publication, concurrency, immutable-version) are included for every affected boundary and written before the implementation they cover.

**Organization**: Grouped by user story (US1–US6), in priority order. Each story is an independently testable increment. US6 is stub/mock only (interface + fixtures, no real AI).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- Story labels: US1–US6. Setup/Foundational/Polish tasks have no story label.

## Path Conventions

Web app: `backend/src/qava/`, `backend/tests/`, `frontend/src/`, `data/`. All paths below are repository-relative.

---

## Phase 1: Setup

**Purpose**: Confirm the baseline is green before adding behavior.

- [X] T001 Run existing backend and frontend suites (`uv run --project backend pytest`; `npm --prefix frontend test`) and record a green baseline so regressions are attributable. Baseline: backend 84 passed (run from `backend/`), frontend 23 passed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared plumbing used by more than one story. Keep minimal.

- [X] T002 [P] Add a shared engine test fixture questionnaire exercising a runtime option source, a nested collection, and money + date/time questions in backend/tests/conftest.py (reused by US1, US3, US5).
- [X] T003 [P] Confirm the OpenAPI regeneration + frontend client generation pipeline runs clean so new endpoints (US2, US4) can be added without hand-editing `frontend/src/api/generated/`.

**Checkpoint**: Baseline green and shared fixture available — story work can begin.

---

## Phase 3: User Story 1 - Complete the Typed Capture Loop (Priority: P1) 🎯 MVP

**Goal**: Runtime-sourced options, nested collections, and every catalogued control (incl. money and date/time) work end to end with stable typed values.

**Independent Test**: Publish a questionnaire using a runtime option source, a nested collection, and money + date/time; complete it in the generic client and confirm each control renders and stores a stable typed value.

### Tests for User Story 1

- [X] T004 [P] [US1] Unit test money/date schema→component compatibility in backend/tests/unit/test_components.py.
- [X] T005 [P] [US1] Unit test per-item collection compose and provenance in backend/tests/unit/test_projection.py.
- [X] T006 [P] [US1] Contract test the component-catalog option provider yields stable choice IDs valid against the answer schema in backend/tests/contract/test_option_provider.py.
- [X] T007 [P] [US1] Integration test a session over the shared multi-shape fixture: options load at runtime, nested collection projects as typed array, money/date stored typed in backend/tests/integration/test_capture_loop.py.

### Implementation for User Story 1

- [X] T008 [P] [US1] Add the named option provider protocol in backend/src/qava/ports/option_provider.py.
- [X] T009 [US1] Implement the component-catalog provider and a provider registry in backend/src/qava/infrastructure/options/ (component_catalog.py, registry.py) (depends on T008).
- [X] T010 [US1] Implement runtime option resolution service in backend/src/qava/application/options.py and invoke it during session evaluation (depends on T009).
- [X] T011 [US1] Extend the dynamic option source + nested-collection schema in data/contracts/v1/ and compile it in backend/src/qava/infrastructure/contracts/definition_pack.py.
- [X] T012 [P] [US1] Add money and date/time compatibility rules in backend/src/qava/domain/components.py (satisfies T004).
- [X] T013 [US1] Add per-item compose mapping for nested collections in backend/src/qava/domain/projection.py within existing depth/item limits (satisfies T005).
- [X] T014 [P] [US1] Map `money_input` (MoneyField) and `date_picker`/`datetime_picker` (DateTimeField) in frontend/src/components/renderers/registry.ts.
- [X] T014a [US1] Support recursive nested `repeating_group` rendering (each nested item field resolves its own control) in frontend/src/components/renderers/RepeatableGroup.vue, with a component test in frontend/tests/component/ (satisfies FR-002 client rendering).

**Checkpoint**: US1 fully functional and independently testable.

---

## Phase 4: User Story 2 - Publish a Result Through an Explicit Adapter (Priority: P2)

**Goal**: Preview a ready result, publish an exact revision through the JSON document adapter, and get an idempotent, receipted, side-effect-free-until-publish flow.

**Independent Test**: Take a session to ready, preview (no side effect), publish once (receipt + stored artifact), repeat the key (no duplicate), and reject a stale revision.

### Tests for User Story 2

- [X] T015 [P] [US2] Contract test `GET .../result/preview` and `POST .../publications` request/response + problem shapes in backend/tests/contract/test_publications.py.
- [X] T016 [P] [US2] Unit test the JSON document adapter validate/preview/publish and receipt shape in backend/tests/unit/test_json_adapter.py.
- [X] T017 [US2] Integration test idempotent republish (no duplicate artifact), stale `expected_revision` → 409, and gate failure → 422 in backend/tests/integration/test_publication_workflow.py.
- [X] T017a [US2] Integration test that an indeterminate adapter outcome records an `outcome_unknown` receipt and reconciles to a terminal status with no duplicate artifact in backend/tests/integration/test_publication_workflow.py.

### Implementation for User Story 2

- [X] T018 [P] [US2] Add the output adapter protocol (validate/preview/publish) in backend/src/qava/ports/output_adapter.py.
- [X] T019 [US2] Add the published-artifact store migration in backend/migrations/versions/ and its repository in backend/src/qava/infrastructure/database/repositories.py (depends on T018).
- [X] T020 [US2] Implement the JSON document adapter writing an immutable `PublishedArtifact` in backend/src/qava/infrastructure/adapters/json_document.py (depends on T018, T019; satisfies T016).
- [X] T021 [US2] Implement preview + idempotent publication service in backend/src/qava/application/publishing.py, reusing `publication_attempts` for idempotency (depends on T020).
- [X] T022 [US2] Add preview and publications request/response schemas in backend/src/qava/api/schemas.py.
- [X] T023 [US2] Add `GET .../result/preview`, `POST .../publications`, and `GET .../publications` endpoints in backend/src/qava/api/routers/sessions.py with role enforcement (depends on T021, T022; satisfies T015, T017).
- [X] T023a [US2] Represent an indeterminate adapter outcome as a resolvable `outcome_unknown` receipt in backend/src/qava/application/publishing.py and add an explicit reconciliation endpoint (`POST .../publications/{publication_id}/reconcile`) in backend/src/qava/api/routers/sessions.py that resolves to a terminal status without a duplicate artifact (depends on T021, T023; satisfies FR-027, T017a).
- [X] T024 [US2] Regenerate OpenAPI (`openapi/qava.openapi.json`) and the frontend client for the new endpoints.
- [X] T025 [P] [US2] Add usePublication composable in frontend/src/composables/usePublication.ts.
- [X] T026 [US2] Add PublicationReview.vue (preview + publish exact revision + receipt) in frontend/src/components/publication/ and a publication route in frontend/src/router/index.ts (depends on T024, T025).

**Checkpoint**: US2 fully functional; a ready session can be published safely.

---

## Phase 5: User Story 3 - Trust Explainable Health (Priority: P3)

**Goal**: Confidence, consistency, and specificity become fixed, built-in, inspectable rules with concrete attention items.

**Independent Test**: Scenarios for weak evidence, contradiction, and imprecision move the correct dimension and emit an attention item; validity can include an adapter dry run.

### Tests for User Story 3

- [X] T027 [P] [US3] Unit test confidence (weak evidence), consistency (contradiction), and specificity (imprecision) rule outputs + attention items in backend/tests/unit/test_health.py.
- [X] T028 [P] [US3] Integration test that health changes and attention surface after answer edits in backend/tests/integration/test_health_rules.py.

### Implementation for User Story 3

- [X] T029 [US3] Replace placeholder confidence/consistency/specificity with fixed inspectable rules and evidence-linked attention items in backend/src/qava/domain/health.py, keeping the existing author-configured headline weights and readiness gates intact (satisfies T027).
- [X] T030 [US3] Add an optional adapter validation dry run to the validity dimension via the output adapter port in backend/src/qava/domain/health.py (or the health evaluation seam) (depends on T018, T029).

**Checkpoint**: Every dimension moves only per declared rules.

---

## Phase 6: User Story 4 - Author Without Writing Code (Priority: P4)

**Goal**: Explicit confirm/override/reject decision workflow plus a raw JSON path, both through the same publication gate. No bespoke UI.

**Independent Test**: Resolve an ambiguous decision by confirm and by override, block publish while a decision is pending, and confirm the raw JSON path converges on identical validation.

### Tests for User Story 4

- [X] T031 [P] [US4] Contract test the decisions and raw JSON draft endpoints in backend/tests/contract/test_authoring_decisions.py.
- [X] T032 [US4] Integration test confirm/override/reject, publish-blocked-while-pending, and raw-path gate convergence in backend/tests/integration/test_authoring_workflow.py.

### Implementation for User Story 4

- [X] T033 [US4] Add the `AuthoringDecision` record and pending-decision surfacing in backend/src/qava/domain/models.py and backend/src/qava/application/authoring.py.
- [X] T034 [US4] Enforce "no publish with pending blocking decision" in the publication gate in backend/src/qava/application/authoring.py (depends on T033).
- [X] T035 [US4] Add `POST .../decisions` and `PUT .../raw` endpoints (same gate) in backend/src/qava/api/routers/questionnaires.py and schemas in backend/src/qava/api/schemas.py (depends on T033, T034; satisfies T031, T032).
- [X] T036 [US4] Regenerate OpenAPI and the frontend client for the new authoring endpoints.

**Checkpoint**: Backend self-service authoring works via both routes.

---

## Phase 7: User Story 5 - Qava Authors Qava (Priority: P5)

**Goal**: A bootstrapped meta-questionnaire + registry adapter let the builder run on the engine, rendered by the existing runtime client.

**Independent Test**: Author a five-question questionnaire through the meta-questionnaire, publish via the registry adapter (new immutable version + `{id, version}` receipt), and run it.

### Tests for User Story 5

- [X] T037 [P] [US5] Contract test the registry adapter receipt (`questionnaire:{id}@{version}`) and new-version immutability in backend/tests/contract/test_registry_adapter.py.
- [X] T038 [US5] Integration/e2e test author→publish→run of a five-question questionnaire through Qava itself in backend/tests/integration/test_self_hosted_authoring.py (and/or e2e/tests/).

### Implementation for User Story 5

- [X] T039 [US5] Add the meta output contract (published-questionnaire schema) in data/contracts/v1/ (depends on T011 dynamic options, T033 decisions).
- [X] T040 [US5] Implement the registry adapter writing a new immutable questionnaire version in backend/src/qava/infrastructure/adapters/registry.py (depends on T018; satisfies T037).
- [X] T041 [US5] Add the bootstrapped meta-questionnaire definition in data/definitions/meta/ and a bootstrap step (CLI in backend/src/qava/cli.py) to publish it.
- [X] T042 [US5] Wire `adapter: registry` through the publication service in backend/src/qava/application/publishing.py (depends on T021, T040).
- [X] T043 [US5] Add a route to start a session against the meta-questionnaire reusing InterviewView in frontend/src/router/index.ts (no bespoke builder).

**Checkpoint**: Qava authors Qava end to end.

---

## Phase 8: User Story 6 - Bounded Agent Assistance Seam (Stub/Mock) (Priority: P6)

**Goal**: A complete assistance interface backed by hardcoded fixtures, validated and behind deterministic fallback; a real provider could drop in later.

**Independent Test**: Fixtures return validated proposals; invalid fixtures are rejected; disabling fixtures leaves every path deterministic and correct.

### Tests for User Story 6

- [X] T044 [P] [US6] Unit test fixture proposal validation, policy rejection, and retained audit metadata in backend/tests/unit/test_assistance.py.
- [X] T045 [US6] Integration test deterministic fallback (assistance disabled / fixture absent) yields identical correctness in backend/tests/integration/test_assistance_fallback.py.

### Implementation for User Story 6

- [X] T046 [P] [US6] Add the narrow assistance protocol (component/ranking/question/clarification/extraction) in backend/src/qava/ports/assistance.py.
- [X] T047 [US6] Implement the fixture provider with hardcoded proposals in backend/src/qava/infrastructure/assistance/fixture.py (depends on T046).
- [X] T048 [US6] Implement the assistance service: validate proposals, apply within policy, retain audit metadata via the existing `assistance_proposals` repository, and fall back deterministically in backend/src/qava/application/assistance.py (depends on T047; satisfies T044, T045).
- [X] T049 [US6] Wire fixture assistance behind the existing `assistance_mode` config so disabling it is a no-op path in backend/src/qava/config.py and the evaluation/authoring call sites.

**Checkpoint**: Assistance seam reserved and proven without real AI.

---

## Phase 9: Polish & Cross-Cutting

**Purpose**: Verify the whole feature and guard the deterministic core.

- [X] T050 [P] Verify generated OpenAPI matches the running app and update the contract test in backend/tests/contract/test_openapi.py. Evidence: `qava openapi validate` reports the committed contract and runtime match; the contract suite passed.
- [X] T051 [P] Add component/accessibility tests for PublicationReview and money/date renderers (Qava Cirrus) in frontend/tests/component/. Evidence: `PublicationAndTypedFields.spec.ts` adds four checks, and `SemanticRenderer.spec.ts` covers generic JSON object/array capture for meta authoring; the full frontend suite passed 31 tests.
- [ ] T052 Run the full quickstart in [quickstart.md](quickstart.md) from a clean checkout and record SC-001…SC-008 evidence. Pending: this feature is uncommitted in the current sparse checkout, so no clean checkout can contain this exact candidate yet.
- [ ] T053 Run the existing contract + integration + performance suites and confirm no regression to the deterministic loop (SC-008). Partial evidence: the contract and integration suite passed 65 tests; no dedicated performance harness exists in the current tree, so the 100-session target remains unverified.
- [X] T054 Do one last pass to make sure everything works. How are you going to do that? Be inventive. But it needs to work at this point. Does it do what we expect it to do? Everything? How will we know? I just need to be confident, I don't need to make new tests, but I do need to know it will work when I start manual testing. Evidence: full browser journey passed at desktop, mobile, and reduced-motion viewports; production build passed; backend contract/integration checks passed; frontend unit/component checks, typecheck, lint, contract validation, and OpenAPI parity are green.

---

## Dependencies & Execution Order

- **Setup (T001) → Foundational (T002–T003) → Stories in priority order (US1→US6) → Polish (T050–T053).**
- Cross-story dependency: the `output_adapter` port (T018, US2) is reused by US3 validity dry-run (T030) and the US5 registry adapter (T040); the meta contract (T039, US5) depends on US1 dynamic options (T011) and US4 decisions (T033).
- Each story is otherwise self-contained and independently testable at its checkpoint.

## Parallel Opportunities

- Within a story, `[P]` tasks touch different files: e.g., US1 tests T004–T007 run together; US1 T008/T012/T014 are parallelizable; US2 T025 parallel to backend work; US6 T046 parallel to its tests.
- Tests within each story's "Tests" block are all `[P]` and should be written first and observed failing.

## MVP Scope

**US1 alone** (Phase 3) is the minimum viable increment: it completes the typed capture loop and unlocks the self-hosting prerequisites. Add US2 for a demonstrable publish, then proceed by priority.
