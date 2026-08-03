# Feature Specification: Deterministic Runtime Hardening

**Feature Branch**: `002-deterministic-runtime-hardening`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "Make the deterministic slice internally trustworthy by unifying session evaluation, repairing skip and navigation semantics, establishing one authoritative API contract and migration mechanism, and closing the highest-value test gaps."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trust Every Deterministic Session Decision (Priority: P1)

As a respondent, I can answer, skip when permitted, navigate to unresolved output needs, resume, and inspect progress knowing that every visible session value and available action comes from one consistent evaluation of the published questionnaire and accepted session state.

**Why this priority**: The deterministic interview is the proven product boundary. Conflicting interpretations of applicability, progress, projection, health, or navigation would make its output and controls untrustworthy even when individual calculations appear correct.

**Independent Test**: Run a questionnaire containing required, optional, conditional, and navigable questions. Answer and replace values, skip only permitted questions, navigate to an unresolved need, and resume the session. Verify that active questions, projection, unresolved needs, progress, health, readiness, permitted actions, and the selected next interaction remain mutually consistent after every operation.

**Acceptance Scenarios**:

1. **Given** a published questionnaire and session snapshot, **When** the session is read or mutated, **Then** one deterministic evaluation produces the active questions, canonical projection, unresolved output needs, progress, health, readiness, permitted actions, and next interaction returned to the user.
2. **Given** an answer change makes another question inapplicable, **When** the new session state is evaluated, **Then** that question is excluded consistently from selection, projection, unresolved needs, progress, health, and readiness while retained audit evidence is not treated as active evidence.
3. **Given** an optional interaction that permits skipping, **When** the respondent skips it, **Then** the skip is retained, the revision advances once, and the same interaction is not immediately selected again unless a later state change makes it eligible again under declared rules.
4. **Given** a required interaction or another interaction for which skipping is prohibited, **When** the session view is produced, **Then** skip is not offered and a direct skip attempt is rejected without advancing the revision.
5. **Given** an unresolved output need with a declared question, **When** the respondent navigates to that need, **Then** the corresponding eligible interaction becomes current and the navigation decision survives the complete response calculation.
6. **Given** a navigation target that is unknown or currently inapplicable, **When** navigation is requested, **Then** the request is rejected without changing session state.

---

### User Story 2 - Rely on One Public API Contract (Priority: P2)

As a client developer, I can rely on the published API description because requests, responses, errors, permissions, and available operations match the running application exactly.

**Why this priority**: Generated clients and browser behavior are only trustworthy when the declared contract cannot silently diverge from runtime behavior.

**Independent Test**: Produce the public API description from the running application and compare all supported paths, operations, request shapes, response shapes, and shared schemas with the checked-in contract. Exercise representative valid and invalid requests and verify that their payloads conform to the same definitions.

**Acceptance Scenarios**:

1. **Given** the checked-in API contract, **When** the running application publishes its API description, **Then** all supported paths, operations, request schemas, response schemas, and shared component schemas are equivalent.
2. **Given** an invalid request, **When** it reaches an API boundary, **Then** the returned problem response conforms to the declared error contract without endpoint-specific ad hoc shapes.
3. **Given** an endpoint declared in the public contract, **When** contract verification runs, **Then** the endpoint must exist at runtime or verification fails.
4. **Given** a runtime endpoint not declared in the public contract, **When** contract verification runs, **Then** verification fails rather than allowing an undocumented operation.

---

### User Story 3 - Reproduce Storage State Reliably (Priority: P3)

As an operator or contributor, I can initialize a clean database and upgrade an existing database through one authoritative migration history, without a second schema definition creating drift.

**Why this priority**: Two schema authorities can produce databases that look initialized but cannot be upgraded or reproduced safely.

**Independent Test**: Initialize an empty database through the supported migration workflow, start the application against it, and rerun the migration workflow. Verify that the schema is at the declared head revision and no tables are recreated or reported as untracked.

**Acceptance Scenarios**:

1. **Given** an empty supported database, **When** initialization runs, **Then** the complete schema is created and recorded at the current migration revision.
2. **Given** a database at the current migration revision, **When** application startup and migration verification run, **Then** neither path attempts to recreate existing tables.
3. **Given** a schema change, **When** it is introduced, **Then** it is represented once in the migration history and no duplicate embedded schema definition requires synchronization.
4. **Given** test setup and local application startup, **When** either creates storage, **Then** both use the same migration authority and produce equivalent schemas.

### Edge Cases

- A skipped optional question later becomes inapplicable and then applicable again after an earlier answer changes.
- Multiple questions serve one output need, including one answered question and one skipped question.
- Navigation targets a need served by multiple eligible questions.
- Navigation targets a question whose applicability changes between the request and the revision-checked mutation.
- Two clients attempt skip, navigation, or answer changes from the same prior revision.
- A retained answer becomes inactive because its applicability condition is no longer satisfied.
- The checked-in API contract and runtime contract differ only in required fields, status codes, error schemas, or operation metadata rather than path names.
- A database contains application tables but lacks migration revision metadata from an older initialization path.
- Draft deletion is requested for an existing draft and for an unknown draft.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST derive active questions, canonical projection, provenance, unresolved output needs, progress, health, readiness, permitted actions, and next interaction from one deterministic session evaluation.
- **FR-002**: All session reads and accepted mutations MUST return results from the same evaluation rules and MUST NOT independently reinterpret answer presence, applicability, or output-need satisfaction.
- **FR-003**: Session evaluation MUST distinguish retained audit evidence from currently active evidence and MUST exclude inactive evidence from projection, satisfaction, progress, health, readiness, and next-interaction decisions.
- **FR-004**: The system MUST retain a skip disposition for a permitted skipped interaction so that the same unchanged interaction is not immediately selected again.
- **FR-005**: The system MUST define skipping as permitted only for optional interactions unless a published rule explicitly permits otherwise.
- **FR-006**: The session view MUST expose the skip action only when the current interaction is permitted to be skipped.
- **FR-007**: A prohibited skip request MUST be rejected without changing answers, dispositions, navigation state, revision, projection, or health.
- **FR-008**: An accepted skip MUST advance the session revision exactly once and retain audit evidence identifying the skipped interaction and actor.
- **FR-009**: Navigation to an unresolved output need MUST select a corresponding currently eligible interaction and MUST affect the complete session view returned by that mutation.
- **FR-010**: Navigation to an unknown, resolved, or inapplicable target MUST be rejected without changing the authoritative session state.
- **FR-011**: Answer, skip, and navigation mutations MUST all enforce expected-revision concurrency and reject stale mutations without overwriting newer state.
- **FR-012**: The public API contract MUST be generated from or fully verified against the runtime request and response definitions so that one source is authoritative.
- **FR-013**: Every public endpoint MUST declare typed request, success-response, and applicable problem-response shapes.
- **FR-014**: Contract verification MUST compare the complete supported path and shared-schema surface, not only API title, version, or description.
- **FR-015**: Generated clients MUST consume the same authoritative contract verified against the running application.
- **FR-016**: The system MUST use one migration history as the authoritative definition of persistent schema.
- **FR-017**: Application startup, local setup, and automated test setup MUST initialize or upgrade storage through the same migration authority.
- **FR-018**: The system MUST NOT retain a second independently maintained table-definition representation after migration unification.
- **FR-019**: Existing databases created before migration unification MUST have a documented, testable path to establish their correct migration revision without destroying retained data.
- **FR-020**: Draft deletion MUST actually remove an existing mutable draft and return not-found behavior for an unknown draft.
- **FR-021**: Automated integration coverage MUST verify skip advancement, prohibited skip rejection, navigation target selection, stale skip/navigation rejection, conditional-answer invalidation, actual draft deletion, and complete API contract equality.
- **FR-022**: Tests for required endpoints MUST fail when those endpoints are unavailable and MUST NOT skip based on endpoint availability.
- **FR-023**: This feature MUST preserve existing accepted-answer validation, immutable questionnaire versions, projection provenance, health dimensions, stale-write protection, and the generic client contract.
- **FR-024**: This feature MUST NOT add result publication, bounded assistance, self-hosted authoring, new output adapters, or unrelated user-interface capabilities.

### Constitution Alignment *(mandatory)*

- **Output Contract Impact**: The output contract remains authoritative. Unified evaluation ensures applicability and output-need satisfaction are interpreted once across projection, progress, health, readiness, and selection.
- **Typed Interaction Impact**: Existing answer schemas, stable machine values, and component specifications remain unchanged. Skip availability and navigation targets become truthful typed session actions rather than client assumptions.
- **AI Policy Boundary**: No assistance behavior is introduced. All behavior in this feature is deterministic, auditable, and complete without AI.
- **Projection and Health**: Every accepted answer, permitted skip, or navigation action returns one internally consistent evaluation. Inactive evidence cannot satisfy projection or health, and failures remain explicit.
- **Publication and Stability**: Result publication remains out of scope. Immutable questionnaire versions, revision concurrency, session resume, and interaction audit evidence must be preserved while migration authority is unified.

### Key Entities

- **Session Evaluation**: The complete deterministic interpretation of one immutable questionnaire version and one authoritative session snapshot, including active evidence, projection, unresolved needs, progress, health, actions, and next interaction.
- **Interaction Disposition**: Session-retained state describing whether an interaction was answered or permissibly skipped and the revision at which that occurred. *(Implementation name: `SkipDisposition`. Feature 002 scope covers skip dispositions only; answer disposition is implicit in the answers map. The "answered" arm is not a separate persisted record.)*
- **Navigation Intent**: A revision-checked request to focus a declared eligible interaction associated with a section or unresolved output need. *(Implementation name: `NavigationFocus`.)*
- **Public API Contract**: The authoritative description of supported operations, typed requests, typed responses, errors, and permissions.
- **Migration History**: The ordered authoritative record of persistent schema creation and changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 100% of tested session states, projection, unresolved needs, progress, health, readiness, actions, and next interaction agree on which evidence and questions are active.
- **SC-002**: In automated tests, every permitted skip advances revision once and selects a different eligible interaction or completes the interview; every prohibited skip advances revision zero times.
- **SC-003**: In automated tests, 100% of valid unresolved-need navigation requests make a corresponding eligible interaction current, while invalid targets leave state unchanged.
- **SC-004**: Complete contract comparison reports zero differences between the checked-in client-generation contract and the running application's supported paths and shared schemas.
- **SC-005**: A clean database reaches the current migration revision successfully, and a repeated migration run completes without schema changes or errors.
- **SC-006**: Storage created by test setup and local application setup has identical tables, constraints, and migration revision metadata.
- **SC-007**: All mandatory deterministic boundary tests execute without availability-based skips, with 100% passing before the feature is considered complete.
- **SC-008**: Existing deterministic browser tests continue to pass across desktop, mobile, and reduced-motion configurations without questionnaire-specific client changes.
- **SC-009**: Contributors maintain one session-evaluation rule set, one public API contract authority, and one persistent-schema authority after completion.

## Assumptions

- Existing published questionnaires and accepted session answers remain compatible; this feature hardens interpretation and lifecycle behavior rather than changing answer schemas.
- Optional interactions may be skipped by default; required interactions may not be skipped unless a future published policy explicitly adds that capability.
- When several eligible questions serve one navigation target, existing deterministic ordering selects among them.
- Navigation focus is session state that may be cleared after the targeted interaction is answered, skipped, or becomes inapplicable.
- Existing databases may require a one-time revision-stamping or equivalent reconciliation step after their schema is verified against the initial migration.
- The checked-in contract may remain as a review artifact, but it cannot be maintained independently from runtime definitions; automated equality is required if both forms remain.
- Publication, assistance, authoring UI, and release packaging remain governed by their existing deferred lifecycle decisions.
