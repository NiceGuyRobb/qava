# Tasks: Structured Input UX

**Input**: Design documents from `/specs/006-structured-input-ux/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), and [component-presentation.md](contracts/component-presentation.md)

**Tests**: Tests cover the affected typed-renderer, definition-contract, and immutable-publication boundaries. Existing session mapping, projection, health, persistence, API, and OpenAPI behavior are unchanged.

**Organization**: Tasks are organized into file-owned vertical slices so a Copilot agent can make one coherent change, run its nearest validation, and avoid conflicts with another agent editing the same file.

## Phase 1: Setup and Artifact Corrections

**Purpose**: Establish an accurate implementation baseline before feature work begins.

- [X] T001 Remove the duplicate template source-tree and Complexity Tracking remainder after the completed plan in `specs/006-structured-input-ux/plan.md`
- [X] T002 Correct the advanced-mode rule so absent declarations permit advanced JSON while malformed or unsupported declarations block publication in `specs/006-structured-input-ux/contracts/component-presentation.md`
- [X] T003 Run the current renderer and authoring-validation baselines using `frontend/tests/component/SemanticRenderer.spec.ts`, `backend/tests/unit/test_definition.py`, `backend/tests/integration/test_authoring_workflow.py`, and `backend/tests/contract/test_data_contracts.py`

---

## Phase 2: Foundational Shared Descriptor Model

**Purpose**: Establish the shared descriptor vocabulary before a renderer tries to consume it.

**Checkpoint**: `StructuredForm`, `RepeatableGroup`, and `NestedFieldList` can receive one descriptor model for all supported nested controls.

- [X] T004 Define `multi_select`, `measurement`, help-text, example, and validation descriptor shapes in `frontend/src/components/renderers/registry.ts`
- [X] T005 Extend recursive descriptor value types and default-value construction for multi-select and measurement fields in `frontend/src/components/renderers/NestedFieldList.vue`

---

## Phase 3: User Story 1 - Complete Structured Answers Without JSON (Priority: P1) MVP

**Goal**: A respondent uses labelled controls for existing structured objects and repeatable items, including multi-select and measurement fields, while submitting the existing typed answer shapes.

**Independent Test**: Mount a structured or repeatable question with declared nested multi-select and measurement fields, interact with the controls, and verify emitted values retain stable option IDs and the declared measurement object shape without a JSON textarea.

### Tests for User Story 1

- [X] T006 [US1] Add one ordered renderer test slice for nested multi-select, measurement value/unit emission, local field feedback, and raw-JSON fallback prevention in `frontend/tests/component/SemanticRenderer.spec.ts`

### Implementation for User Story 1

- [X] T007 [US1] Derive multi-select options, measurement unit options, field help/example metadata, and declared numeric constraints from component props and answer-schema properties in `frontend/src/components/renderers/registry.ts`
- [X] T008 [US1] Render accessible nested multi-select checkboxes and measurement value/unit controls, preserving option IDs and sibling values while giving local feedback only for required selection, missing unit, non-finite values, and declared numeric bounds in `frontend/src/components/renderers/NestedFieldList.vue`
- [X] T009 [US1] Route structured-form field rendering through the shared recursive descriptor renderer rather than a duplicate scalar-only implementation in `frontend/src/components/renderers/StructuredForm.vue`
- [X] T010 [US1] Preserve nested multi-select and measurement values when adding or removing repeated items in `frontend/src/components/renderers/RepeatableGroup.vue`
- [X] T011 [US1] Define the `target_area` value/unit answer schema and preserve its existing mapping target in `data/definitions/custom-home-intake/v1/questions/structure.json`
- [X] T012 [US1] Run `npm test -- SemanticRenderer.spec.ts` and `npm run typecheck` from `frontend/package.json`

**Checkpoint**: Current custom-home structured and repeated questions with complete declarations render ordinary controls and emit valid typed values; no mapping, projection, health, or API behavior changes.

---

## Phase 4: User Story 2 - Use Raw JSON Only Deliberately (Priority: P1)

**Goal**: Fully declared forms never silently show a JSON editor; truly unconstrained object and collection answers retain a clearly identified advanced input mode.

**Independent Test**: Compare a complete structured declaration with an unconstrained object/array declaration and verify only the latter renders the labelled advanced JSON path while retaining object/array parse feedback.

### Tests for User Story 2

- [X] T013 [US2] Add advanced-mode labels, invalid JSON shape/error, and completed-declaration no-textarea regression assertions in `frontend/tests/component/SemanticRenderer.spec.ts`

### Implementation for User Story 2

- [X] T014 [US2] Label the unconstrained object JSON textarea as an advanced input mode while preserving current parse and object-shape feedback in `frontend/src/components/renderers/StructuredForm.vue`
- [X] T015 [US2] Label the unconstrained array JSON textarea as an advanced input mode while preserving current parse and array-of-objects feedback in `frontend/src/components/renderers/RepeatableGroup.vue`
- [X] T016 [US2] Run `npm test -- SemanticRenderer.spec.ts` from `frontend/package.json`

**Checkpoint**: JSON remains available for genuinely open-ended answers, but no complete respondent form is silently degraded to JSON.

---

## Phase 5: User Story 3 - Author Predictable Structured Questions (Priority: P2)

**Goal**: Authors receive field-specific validation before publication when a structured declaration cannot render safely, and may provide presentation-only help and examples for supported fields.

**Independent Test**: Create compatible and incompatible structured declarations through both guided and raw draft authoring; verify the compatible draft can publish, while each incompatible field produces a deterministic issue that blocks publication.

### Tests for User Story 3

- [X] T017 [P] [US3] Add unit coverage for duplicate keys, unsupported nested components, missing select options, and incompatible multi-select/measurement shapes in `backend/tests/unit/test_definition.py`
- [X] T018 [P] [US3] Add contract coverage that catalog props schemas are applied to each checked-in question component declaration in `backend/tests/contract/test_data_contracts.py`
- [X] T019 [P] [US3] Add guided-update and raw-draft publication-blocking cases for structured component compatibility issues in `backend/tests/integration/test_authoring_workflow.py`
- [X] T020 [P] [US3] Add help-text and example rendering cases that verify presentation metadata does not coerce emitted values in `frontend/tests/component/SemanticRenderer.spec.ts`

### Implementation for User Story 3

- [X] T021 [US3] Validate each checked-in question's `component.props` against its named catalog `props_schema` while loading the definition pack in `backend/src/qava/infrastructure/contracts/registry.py`
- [X] T022 [US3] Validate structured and repeatable field declarations and emit field-specific `DefinitionIssue` values during draft compilation and publication validation in `backend/src/qava/domain/definition.py`
- [X] T023 [US3] Define restrictive props schemas for `structured_form` and `repeatable_group` field declarations in `data/components/catalog.v1.json`
- [X] T024 [US3] Render optional help text and examples beside supported nested controls without exposing machine identifiers in `frontend/src/components/renderers/NestedFieldList.vue`
- [X] T025 [US3] Add only definition metadata required for the checked-in custom-home pack to satisfy the new component-props validation in `data/definitions/custom-home-intake/v1/questions/household.json`, `data/definitions/custom-home-intake/v1/questions/outdoors.json`, and `data/definitions/custom-home-intake/v1/questions/structure.json`
- [X] T026 [US3] Run the focused frontend, backend unit, authoring integration, and data-contract checks from `frontend/package.json`, `backend/tests/unit/test_definition.py`, `backend/tests/integration/test_authoring_workflow.py`, and `backend/tests/contract/test_data_contracts.py`

**Checkpoint**: Both authoring routes surface the same deterministic component issue and reject publication until the declaration is corrected; supplemental guidance leaves typed values untouched.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Verify the integrated respondent and authoring paths while preserving Qava invariants.

- [X] T027 [P] Verify the real session workflow for household members and home structure, including result-preview updates, using `specs/006-structured-input-ux/quickstart.md`
- [X] T028 [P] Verify keyboard operation, mobile-width layout, 200% zoom, and reduced-motion behavior for nested controls in `frontend/src/components/renderers/NestedFieldList.vue`, `frontend/src/components/renderers/StructuredForm.vue`, and `frontend/src/components/renderers/RepeatableGroup.vue`
- [ ] T029 Run `npm test`, `npm run lint`, `npm run typecheck`, and `npm run build` from `frontend/package.json`, then `uv run --project backend pytest`, `uv run --project backend ruff check backend/src backend/tests`, and `uv run --project backend pyright` from `backend/pyproject.toml`
- [ ] T030 Execute the five-participant structured-question usability check and advanced-JSON recognition review against the scenarios in `specs/006-structured-input-ux/quickstart.md`
- [X] T031 Verify no duplicate/reorder controls, unit conversion, API changes, database migrations, or published-version/session mutation were introduced by reviewing `specs/006-structured-input-ux/plan.md`

---

## Dependencies and Execution Order

```text
T001-T003
  -> T004-T005
  -> US1: T006-T012
  -> US2: T013-T016
  -> US3: T017-T026
  -> T027-T031
```

### User Story Dependencies

- **US1 (P1)** depends on the shared descriptor model in T004-T005 and delivers the MVP, including local field feedback required by FR-006.
- **US2 (P1)** follows US1 because it changes the same renderer components and component-test file; it is a separate, independently testable fallback behavior slice.
- **US3 (P2)** depends on the completed field contract from US1. Its backend boundary tests in T017-T019 and frontend metadata test in T020 can be created in parallel because each owns a different file.

### Parallel Opportunities

- T017, T018, T019, and T020 can proceed in parallel: each changes a distinct test file.
- T027 and T028 can proceed in parallel after T026: one follows the real session workflow and the other is visual/accessibility validation.
- All remaining tasks are intentionally sequential because the same Copilot agent should retain context across their shared source or test file.

## Parallel Example: User Story 3

```text
Task: "Add component compatibility unit cases in backend/tests/unit/test_definition.py"
Task: "Add checked-in definition component-props contract cases in backend/tests/contract/test_data_contracts.py"
Task: "Add guided and raw authoring publication cases in backend/tests/integration/test_authoring_workflow.py"
Task: "Add help/example rendering cases in frontend/tests/component/SemanticRenderer.spec.ts"
```

## Implementation Strategy

### MVP First

1. Complete T001-T005.
2. Complete US1 through T012.
3. Stop and run the focused renderer suite, typecheck, and one real custom-home session.
4. Deliver the no-JSON respondent experience before authoring-schema hardening.

### Incremental Delivery

1. US1 provides ordinary controls and narrow local feedback for existing structured questions.
2. US2 makes the remaining JSON capability deliberate and understandable.
3. US3 prevents new malformed declarations from recreating the problem and supports presentation guidance.
4. Final validation confirms existing session and immutable-publication guarantees remain intact.

## Notes

- Every task follows the required checkbox, task ID, story-label, and exact-path format.
- The feature intentionally excludes duplicate/reorder actions, chip-only multi-select styling,
  arbitrary schema editing, unit conversion, migrations, endpoints, and OpenAPI changes.
- Local field feedback is intentionally limited; server-side JSON Schema validation remains authoritative and this feature must not add a generic client JSON Schema validator.
