# Tasks: Declared Programme Renderer

**Input**: Design documents from `/specs/007-declared-programme-renderer/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md), and
[declared-programme.md](contracts/declared-programme.md)

**Tests**: Tests are required for the affected component-compatibility, answer-validation,
definition-pack, authoring/publication, direct-mapping/projection, and immutable-version
boundaries. No API or persistence contract changes are planned.

**Organization**: Tasks are grouped by user story. The frontend renderer is a generic client
component; the checked-in custom-home definition is its first consumer only.

## Phase 1: Setup and Contract Foundation

**Purpose**: Establish a stable generic component vocabulary and baseline checks before any
respondent-facing behavior is changed.

- [X] T001 Run the renderer, definition-pack, definition-validation, authoring, answer-validation, and interview baselines in `frontend/tests/component/SemanticRenderer.spec.ts`, `backend/tests/unit/test_definition_pack.py`, `backend/tests/unit/test_definition.py`, `backend/tests/unit/test_answer_and_components.py`, `backend/tests/integration/test_authoring_workflow.py`, and `backend/tests/integration/test_interview_workflow.py`
- [X] T002 Define the restrictive domain-neutral `declared_programme` catalog props schema and remove the legacy `room_programme` catalog entry in `data/components/catalog.v1.json`

---

## Phase 2: Foundational Definition Contract

**Purpose**: Declare one explicit, machine-stable programme answer contract that the renderer,
server validation, and direct mapping can share.

**Checkpoint**: The checked-in consumer has stable item/status/detail values, a compatible
`selections` schema, and retains its existing `/rooms/programme` mapping target.

- [X] T003 Migrate the checked-in programme question to `declared_programme` with labelled stable values, declared groups/statuses/details, and an explicit `selections` answer schema in `data/definitions/custom-home-intake/v1/questions/rooms.json`
- [X] T004 Add compiled-pack assertions for the declared programme props, explicit answer schema, and unchanged direct mapping target in `backend/tests/unit/test_definition_pack.py`
- [X] T005 Run the focused definition-pack and checked-in catalog contract checks in `backend/tests/unit/test_definition_pack.py` and `backend/tests/contract/test_data_contracts.py`

---

## Phase 3: User Story 1 - Complete a Declared Programme (Priority: P1) MVP

**Goal**: A respondent completes a valid declared programme with grouped status controls and
optional typed details, without seeing an Advanced JSON textarea.

**Independent Test**: Mount a valid programme declaration, choose statuses in multiple groups,
enter an optional detail, and verify the emitted object contains stable `item_id`, `status`, and
detail values only; submit it through a session and verify it maps unchanged to `/rooms/programme`.

### Tests for User Story 1

- [X] T006 [P] [US1] Add valid declared-programme rendering and stable item/status/detail emission coverage, including no-textarea assertions, in `frontend/tests/component/SemanticRenderer.spec.ts`
- [X] T007 [P] [US1] Add a full session submission case that asserts revision advancement, unchanged direct projection to `/rooms/programme`, health refresh, and next-interaction recalculation in `backend/tests/integration/test_interview_workflow.py`

### Implementation for User Story 1

- [X] T008 [US1] Create the domain-neutral grouped status and optional-detail control component with typed `selections` emission in `frontend/src/components/renderers/DeclaredProgramme.vue`
- [X] T009 [US1] Register `declared_programme`, derive only validated generic groups/statuses/details props, and return the standard unsupported result for malformed published contracts in `frontend/src/components/renderers/registry.ts`
- [X] T010 [US1] Add generic duplicate `selections[].item_id` rejection after JSON Schema validation in `backend/src/qava/domain/answers.py`
- [X] T011 [US1] Add answer-validation cases for duplicate item IDs, undeclared item/status values, and invalid detail values in `backend/tests/unit/test_answer_and_components.py`
- [X] T012 [US1] Run the focused component, answer-validation, definition-pack, and interview checks from `frontend/tests/component/SemanticRenderer.spec.ts`, `backend/tests/unit/test_answer_and_components.py`, `backend/tests/unit/test_definition_pack.py`, and `backend/tests/integration/test_interview_workflow.py`

**Checkpoint**: A declared programme is captured as typed evidence and reaches the existing result,
health, and next-interaction loop with no component-specific API or engine behavior.

---

## Phase 4: User Story 2 - Publish Only Renderable Programme Declarations (Priority: P2)

**Goal**: Authors receive deterministic issues for incomplete or incompatible programme
declarations before publication, across checked-in packs and both draft authoring paths.

**Independent Test**: Validate a complete programme declaration and malformed variants through
guided updates, raw replacement, and the checked-in pack contract; only the complete declaration
publishes, while every malformed declaration identifies its failing part.

### Tests for User Story 2

- [X] T013 [P] [US2] Add definition-validation cases for missing or duplicate group/item/status/detail values, unsupported detail controls, and incompatible `selections` schema shapes in `backend/tests/unit/test_definition.py`
- [X] T014 [P] [US2] Add guided-update and raw-replacement publication-blocking cases for declared programme issues in `backend/tests/integration/test_authoring_workflow.py`
- [X] T015 [P] [US2] Add a checked-in definition-pack contract case that fails a semantic declared-programme mismatch while generic JSON Schema still passes in `backend/tests/contract/test_data_contracts.py`
- [X] T016 [P] [US2] Add malformed published programme props coverage that asserts the explicit unsupported state, never Advanced JSON fallback, in `frontend/tests/component/SemanticRenderer.spec.ts`

### Implementation for User Story 2

- [X] T017 [US2] Add shared domain-neutral programme declaration and answer-schema compatibility validation to the existing publication validation flow in `backend/src/qava/domain/definition.py`
- [X] T018 [US2] Apply the same programme semantic validation when validating checked-in definition packs in `backend/src/qava/infrastructure/contracts/registry.py`
- [X] T019 [US2] Run the focused unit, authoring integration, data-contract, and component checks from `backend/tests/unit/test_definition.py`, `backend/tests/integration/test_authoring_workflow.py`, `backend/tests/contract/test_data_contracts.py`, and `frontend/tests/component/SemanticRenderer.spec.ts`

**Checkpoint**: Incomplete programme declarations are stopped before publication, and a malformed
published contract remains visible as unsupported rather than silently becoming an advanced input.

---

## Phase 5: User Story 3 - Reuse the Declared Programme Contract (Priority: P3)

**Goal**: A second declarative vocabulary proves the renderer uses only published generic props,
not custom-home labels, question IDs, mapping paths, or runtime branches.

**Independent Test**: Mount a second valid programme declaration with different groups, item
values, labels, and statuses; confirm it emits only that declaration's stable values even when
display labels change.

### Tests for User Story 3

- [X] T020 [US3] Add a second unrelated programme declaration and label-versus-value regression coverage in `frontend/tests/component/SemanticRenderer.spec.ts`

### Implementation for User Story 3

- [X] T021 [US3] Refine generic programme prop types and derivation as required by the second-declaration regression without introducing questionnaire-specific branches in `frontend/src/components/renderers/registry.ts`
- [X] T022 [US3] Run the second-declaration component regression and frontend typecheck from `frontend/tests/component/SemanticRenderer.spec.ts` and `frontend/package.json`

**Checkpoint**: The same component renders different published programme vocabularies while stored
machine values remain independent of display labels.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Verify the integrated respondent, authoring, direct-mapping, and immutable-version
paths without expanding engine scope.

- [X] T023 [P] Execute the focused automated validation matrix in `specs/007-declared-programme-renderer/quickstart.md`
- [ ] T024 [P] Run the manual fresh-version browser scenario and prior-version session compatibility check in `specs/007-declared-programme-renderer/quickstart.md`
- [X] T025 Verify the change set introduces no endpoints, OpenAPI changes, database migrations, persistence changes, mapping/projection/health branches, or custom-home runtime logic against `specs/007-declared-programme-renderer/plan.md`

---

## Dependencies and Execution Order

```text
T001-T002
  -> T003-T005
  -> US1: T006-T012
  -> US2: T013-T019
  -> US3: T020-T022
  -> T023-T025
```

### User Story Dependencies

- **US1 (P1)** depends on the shared catalog and checked-in declaration contract from T002-T005;
  it delivers the MVP typed respondent experience and standard session projection.
- **US2 (P2)** follows US1 because the declaration and renderer contract must be concrete before
  its validation rules can be verified; its boundary tests can be authored in parallel.
- **US3 (P3)** follows US1 because it proves the delivered renderer is generic; it does not add a
  second runtime implementation.

### Parallel Opportunities

- T006 and T007 can proceed in parallel because they own distinct frontend and backend test files.
- T013, T014, T015, and T016 can proceed in parallel because each owns a distinct test file.
- T023 and T024 can proceed in parallel after T022: automated checks and manual version/session
  validation are independent.

## Parallel Example: User Story 2

```text
Task: "Add programme declaration unit cases in backend/tests/unit/test_definition.py"
Task: "Add guided/raw authoring cases in backend/tests/integration/test_authoring_workflow.py"
Task: "Add checked-in pack semantic contract case in backend/tests/contract/test_data_contracts.py"
Task: "Add unsupported published programme component case in frontend/tests/component/SemanticRenderer.spec.ts"
```

## Implementation Strategy

### MVP First

1. Complete T001-T005 to establish the stable declaration and explicit answer schema.
2. Complete US1 through T012.
3. Stop and run the focused renderer, answer-validation, definition-pack, and interview checks.
4. Demonstrate a fresh session where the programme maps to `/rooms/programme` without JSON.

### Incremental Delivery

1. US1 provides a fully typed declared-programme respondent flow using existing mapping and session
   semantics.
2. US2 ensures malformed declarations cannot regress respondents to Advanced JSON during future
   authoring.
3. US3 proves the contract remains reusable and free of custom-home runtime coupling.
4. Final validation confirms explicit publication and immutable-version/session behavior remain
   intact.

## Notes

- Every task follows the required checkbox, task ID, story-label, and exact-path format.
- The feature intentionally excludes new endpoints, OpenAPI models, migrations, persistence work,
  mapping/projection/health changes, custom-home engine branches, free-form items, reordering,
  duplication UI, and unit conversion.
- Raw JSON remains the explicit advanced path only for genuinely unconstrained generic objects;
  declared-programme contract failures use the unsupported component state.