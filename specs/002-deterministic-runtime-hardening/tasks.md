# Tasks: Deterministic Runtime Hardening

**Input**: Design documents from `/specs/002-deterministic-runtime-hardening/`

**Branch**: `002-deterministic-runtime-hardening`

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Data model**: [data-model.md](data-model.md) · **Research**: [research.md](research.md) · **Contract**: [contracts/api-contract.md](contracts/api-contract.md) · **Quickstart**: [quickstart.md](quickstart.md)

**Skills required**: Python tasks → `fastapi-python`, `python-best-practices`. Frontend tasks → `vue-best-practices`.

---

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]** — parallelisable (no pending task dependency, different files)
- **[US1/US2/US3]** — user story label (setup and foundational phases have none)
- All tests that exercise a contract, mapping, projection, health, migration, or concurrency boundary are mandatory per the project constitution.

---

## Phase 1: Setup

**Purpose**: Additive Alembic migration for session disposition/focus state. Everything else builds on the existing project scaffold.

- [X] T001 Add Alembic migration `0002_session_disposition_focus`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure evaluator and extended session record are the shared substrate for all three user stories. Both must exist before any mutation path, contract work, or migration tests can proceed.

⚠️ **CRITICAL**: Phases 3–5 cannot begin until T002–T010 are complete.

- [X] T002 [P] Extend `SessionRecord` in `backend/src/qava/domain/models.py`
- [X] T003 [P] Extend `SQLiteSessionRepository` in `backend/src/qava/infrastructure/database/repositories.py`
- [X] T004 Add `evaluate_session(questionnaire, session)` pure function in `backend/src/qava/domain/evaluation.py`
- [X] T005 Add unit test matrix in `backend/tests/unit/test_evaluation.py`
- [X] T006 Replace `_build_session_view` in `backend/src/qava/application/interviewing.py`
- [X] T007 [P] Update `SessionRepository.update_with_revision` protocol in `backend/src/qava/ports/repositories.py`
- [X] T008 [P] Add programmatic Alembic upgrade helper `run_alembic_upgrade(connection)` in `backend/src/qava/infrastructure/database/migrate.py`; remove `_SCHEMA_SQL`
- [X] T009 Update `DatabaseSessionManager.initialize` in `backend/src/qava/infrastructure/database/session.py`
- [X] T010 Update `InMemoryDatabaseSessionManager.initialize` in `backend/tests/integration/conftest.py`

**Checkpoint**: Foundation ready — evaluation is pure and tested, session state model is extended, migration path is unified.

---

## Phase 3: User Story 1 — Trust Every Deterministic Session Decision (Priority: P1)

**Goal**: Every session read and mutation returns one internally consistent evaluation; inactive retained evidence is excluded from all derived fields; the evaluator is the sole derivation path.

**Independent Test**: Run a questionnaire with required, optional, and conditional questions. Answer a question, then change an earlier answer that makes a later question inapplicable. Verify that the inapplicable question's retained answer does not appear in `result.data`, does not count toward `health`, is not in `unresolved_output_needs`, and is not offered as `current_interaction`.

### Tests — User Story 1

- [X] T011 [P] [US1] Add integration test `test_inactive_answer_excluded_after_answer_change`
- [X] T012 [P] [US1] Add integration test `test_session_resume_uses_evaluator`

### Implementation — User Story 1

- [X] T013 [US1] Delete `_unresolved_needs` and `_runtime_interaction` helper functions from `backend/src/qava/application/interviewing.py`

**Checkpoint**: US1 complete — one evaluator, verified by evaluation matrix (T005) and two integration tests (T011, T012).

---

## Phase 4: User Story 2 — Rely on One Public API Contract (Priority: P2)

**Goal**: Typed Pydantic transport models own request/response shapes; `create_app().openapi()` is the sole authority; the committed `openapi/qava.openapi.json` matches runtime exactly; generated frontend types derive from it.

**Independent Test**: Export `openapi/qava.openapi.json` from the running application. Compare it byte-for-byte (after canonical JSON serialisation) with the committed artifact. Exercise a valid and an invalid request body against each session endpoint; assert response shapes match declared schemas.

### Tests — User Story 2

- [X] T014 [P] [US2] Replace `test_fastapi_metadata_matches_contract` with `test_openapi_contract_equals_runtime`
- [X] T015 [P] [US2] Add `test_problem_detail_shapes_conform` in `backend/tests/contract/test_openapi.py`
- [X] T016 [P] [US2] Add `test_draft_deletion_not_found` and `test_draft_deletion_succeeds`

### Implementation — User Story 2

- [X] T017 [US2] Create `backend/src/qava/api/schemas.py` with Pydantic transport models
- [X] T018 [US2] Update `backend/src/qava/api/routers/questionnaires.py` — implement `delete_draft`
- [X] T019 [US2] Update `backend/src/qava/api/routers/sessions.py` with typed request models and `SessionView` response model
- [X] T020 [US2] Add `delete_draft(draft_id: str) -> bool` to `AuthoringService`
- [X] T021 [US2] Export `openapi/qava.openapi.json`; update `frontend/package.json` `api:generate` script
- [X] T022 [US2] Expand `validate_openapi` in `backend/src/qava/cli.py` to deep-compare full document

**Checkpoint**: US2 complete — zero-diff contract test passes, problem shapes conform, draft deletion works, frontend generates from runtime contract.

---

## Phase 5: User Story 3 — Reproduce Storage State Reliably (Priority: P3)

**Goal**: Alembic migration history is the sole schema authority for startup, CLI, and tests; `_SCHEMA_SQL` is removed; clean, repeated, and legacy reconciliation paths are verified.

**Independent Test**: Run `alembic upgrade head` on an empty SQLite file. Start the application against it. Run `alembic upgrade head` again. Query `alembic_version`; the head revision is recorded and no tables were recreated.

### Tests — User Story 3

- [X] T023 [P] [US3] Add `test_clean_migration_reaches_head` in `backend/tests/contract/test_migration.py`
- [X] T024 [P] [US3] Add `test_repeated_migration_is_idempotent` in `backend/tests/contract/test_migration.py`
- [X] T025 [P] [US3] Add `test_file_and_memory_schema_equal` in `backend/tests/contract/test_migration.py`
- [X] T026 [P] [US3] Add `test_legacy_reconcile_stamps_exact_match` and `test_legacy_reconcile_refuses_mismatch`

### Implementation — User Story 3

- [X] T027 [US3] Add `qava db reconcile` sub-command in `backend/src/qava/cli.py`
- [X] T028 [US3] Confirm `_SCHEMA_SQL` removed; delete from `migrate.py` and remove import from `conftest.py`

**Checkpoint**: US3 complete — migration tests pass, embedded SQL removed, reconciliation CLI works.

---

## Phase 6: Polish and End-to-End Regression

**Purpose**: Cross-cutting validation that all three user stories are mutually consistent and the existing deterministic browser journey is unaffected.

### Skip and Navigation Mutation Boundary Tests

- [X] T029 [P] Add skip test cases (permitted/completes/prohibited) — must not use `pytest.skip`: (a) `test_skip_permitted_advances_revision_once`: publish a questionnaire with one required and one optional question; answer the required; skip the optional; expect 200, `result.revision` advanced once, same question absent from next `current_interaction`; assert the audit `RuntimeInteractionRecord` row has `kind="skip"`, `metadata["question_id"]` matching the skipped question, and `actor_id` matching the request identity (FR-008). (b) `test_skip_completes_interview`: publish a questionnaire with one optional question and no required questions; skip it; expect 200, `current_interaction` is `null`, `session.status` is `"completed"` (SC-002 completes-interview branch). (c) `test_skip_prohibited_rejected`: skip a required interaction; expect 422, `result.revision` unchanged, no audit row added.
- [X] T030 [P] Add `test_skip_stale_revision_rejected`
- [X] T031 [P] Add `test_navigation_valid_makes_target_current`
- [X] T032 [P] Add navigation rejection tests
- [X] T033 [P] Add `test_navigation_stale_revision_rejected`
- [X] T034 [P] Add `test_skip_resume_focus_preserved`

### Implementation — Skip and Navigation Mutations

- [X] T035 *(depends on T006)* Update `skip_interaction` in `backend/src/qava/application/interviewing.py` to: (1) evaluate current session state via `evaluate_session`, (2) assert `"skip"` is in `permitted_actions` else raise `ValueError("Skip not permitted")`, (3) persist updated `skip_dispositions` (add entry) alongside answers and focus in `update_with_revision`, (4) append audit `RuntimeInteractionRecord(kind="skip", metadata={"question_id": ...}, actor_id=...)` in the same transaction, (5) return response built from post-update `evaluate_session`
- [X] T036 *(depends on T006)* Update `navigate` in `backend/src/qava/application/interviewing.py` to: (1) evaluate current state via `evaluate_session`, (2) resolve target question from `output_need_id` or `section_id`, (3) assert target is in `evaluation.unresolved_needs` and `evaluation.applicable_question_ids` else raise `ValueError`, (4) persist `NavigationFocus` in `update_with_revision`, (5) append `RuntimeInteractionRecord(kind="navigation")`, (6) return response built from post-update `evaluate_session`

### Frontend Regression

- [X] T037 [P] Regenerate `frontend/src/api/generated/schema.ts` and run `npm --prefix frontend run typecheck`
- [X] T038 [P] Run `npm --prefix frontend run test` — 23/23 Vitest tests pass

### End-to-End Playwright Regression

- [X] T039 Playwright desktop, mobile, reduced-motion — 3/3 pass (SC-008)

### Final Backend Validation

- [X] T040 Run full backend test suite — 84/84 pass, no skips on required endpoints

---

## Dependencies

```
T001 (migration)
  └─> T002, T003 (extended model + repository)
        └─> T004 (evaluator)
              └─> T005 (evaluator tests)
              └─> T006 (wire evaluator into interviewing service)
              └─> T007 (protocol update)
        └─> T008, T009, T010 (Alembic-only init)
              └─> T023–T026 (migration tests)
              └─> T027–T028 (reconcile + cleanup)

Phase 2 complete
  └─> T011–T013 (US1: integration tests + service wiring)
  └─> T017–T022 (US2: schemas, routers, deletion, artifact)
        └─> T014–T016 (US2: contract + deletion tests — run after T021)
  └─> T029–T036 (Phase 6: skip/nav tests + mutations)
        └─> T037–T040 (frontend regression + full suite)
```

**User story independence**: US1 (T011–T013) and US3 (T023–T028) can proceed in parallel once the foundation is complete. US2 (T014–T022) depends on the evaluator being wired (T006) so all endpoints return correct shapes.

**Parallel opportunities within phases**:
- T002 and T003 (different files, Phase 2)
- T005 and T008 (tests vs. infra, Phase 2)
- T011, T012 (independent integration scenarios, Phase 3)
- T014, T015, T016 (contract tests, Phase 4)
- T017, T018, T019, T020 (schemas/routers/service, Phase 4)
- T023, T024, T025, T026 (migration tests, Phase 5)
- T029–T034 (integration boundary tests, Phase 6)
- T037, T038 (frontend regression, Phase 6)

---

## Implementation Strategy

**MVP scope** (minimum to have a trustworthy deterministic core): Phase 1 + Phase 2 + Phase 3 (T001–T013). This establishes the one evaluator, unified session state, and Alembic initialization. US1 is independently testable at T013.

**Full feature**: All phases in order. US2 and US3 can proceed in parallel after the Phase 2 checkpoint.

**Do not start** US2 typed contract work until T006 is complete — routers must return evaluator-derived shapes before schema models are designed around them.
