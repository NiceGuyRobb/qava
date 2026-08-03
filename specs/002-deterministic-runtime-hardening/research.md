# Research: Deterministic Runtime Hardening

## Complete Session Evaluation

**Decision**: Add one pure `evaluate_session(questionnaire, session)` domain function returning an
immutable complete evaluation. Compute applicable questions and active answers first, then pass
that shared interpretation to projection, unresolved-needs, progress, health, actions, and
selection. Persist skip dispositions and navigation focus in the session snapshot.

**Rationale**: The existing domain functions are deterministic but are orchestrated independently
inside `application/interviewing.py`; unresolved-needs and action logic reinterpret answer
presence separately. A single pure owner fixes semantic drift while preserving the constitution's
small `questionnaire + session -> next interaction + result + health` model. Snapshot state makes
resume exact without replaying the interaction table.

**Alternatives considered**:

- Keep `_build_session_view` and patch skip/navigation locally: rejected because applicability,
  satisfaction, action, and selection rules would remain independently interpreted.
- Reconstruct current state from interaction events: rejected as event sourcing beyond the MVP and
  unnecessary when the revisioned session is already authoritative.
- Add separate disposition/navigation tables: rejected because each session has small bounded
  state updated atomically with the same revision; extra joins and repositories add no value.

---

## Skip Disposition Lifecycle

**Decision**: Store a map keyed by question ID containing accepted revision and actor. A permitted
skip suppresses that currently applicable optional question. Suppression ceases when the question
becomes inapplicable; if later applicable again, it may be selected under normal deterministic
ordering. Answering the question removes its skip disposition.

**Rationale**: Audit rows alone do not affect selection, causing immediate reselection. The chosen
lifecycle satisfies the specified re-entry edge case and avoids treating skip as an answer or as
permanent questionnaire mutation.

**Alternatives considered**:

- Store a sentinel answer: rejected because it violates answer schemas and contaminates projection.
- Suppress forever after one skip: rejected because applicability can change and the specification
  explicitly permits later eligibility under declared rules.
- Infer the latest skip by querying audit history: rejected because current view generation would
  depend on I/O and event interpretation rather than one complete snapshot.

---

## Navigation Focus

**Decision**: Persist one optional navigation focus containing target question ID and target
context. Validate it against the pre-mutation evaluation; the response evaluator honors it before
ordinary selection. Clear it after the target is answered, skipped, resolved, or becomes
inapplicable. Multiple eligible questions for one need use existing deterministic ordering.

**Rationale**: The current navigation audit record does not influence the selected interaction.
Persisting the focus in the revisioned row makes navigation observable, resumable, and protected by
the same compare-and-swap as answers and skips.

**Alternatives considered**:

- Return a one-off overridden response without persistence: rejected because resume and subsequent
  reads would disagree.
- Persist only topic ID: rejected because output-need navigation must select an exact eligible
  interaction and survive complete response evaluation.

---

## Mutation Atomicity and Audit

**Decision**: Validate against one pre-mutation evaluation, perform one revision-checked session
update, append audit evidence in the same database transaction, then evaluate the returned snapshot
once. Rejections and stale writes append nothing and advance zero revisions.

**Rationale**: Existing dependency-scoped database sessions already commit or roll back all
repository operations together. Keeping state and audit writes in that transaction preserves exact
revision semantics without a new unit-of-work abstraction.

**Alternatives considered**:

- Append audit before compare-and-swap: rejected because stale requests would leave false evidence.
- Introduce a workflow or command bus: rejected because the current application service already
  owns transactions and only three mutations require the pattern.

---

## Public API Contract Authority

**Decision**: Define typed Pydantic transport models, explicit response/problem models, and stable
operation IDs in FastAPI. Treat `create_app().openapi()` as authority. Export deterministic JSON
to `openapi/qava.openapi.json`, compare the complete normalized artifact to runtime output in
contract tests, and make `openapi-typescript` consume that artifact.

**Rationale**: The checked-in feature-001 YAML is manually maintained while current routers use
raw dictionaries and `response_model=None`; metadata-only tests cannot detect path or schema
drift. Runtime-generated OpenAPI binds validation, serialization, documentation, and client
generation to one owner. A repository-level path avoids coupling live builds to a historical
planning directory.

**Alternatives considered**:

- Keep the YAML authoritative and generate server stubs: rejected because it adds a new
  code-generation toolchain and conflicts with the established FastAPI/Pydantic implementation.
- Maintain runtime and YAML as equal co-authorities: rejected because equality detects drift but
  does not establish which side should be changed on divergence.
- Fetch `/openapi.json` during every frontend build: rejected because reproducible offline
  generation and review require a committed derived artifact.

---

## Contract Equality

**Decision**: Compare the complete deterministic OpenAPI document. Paths, methods, parameters,
request bodies, status responses, security, operation IDs, and all referenced component schemas
remain in scope. Export and validate use the same canonical JSON serializer. Suppress only proven
generator noise (none identified in FastAPI 0.100+ deterministic output).

**Rationale**: Broad normalization hides exactly the required-field, status-code, error-schema,
and operation-metadata differences this feature must catch. Deterministic generation makes direct
structural equality practical without custom exclusion rules.

**Alternatives considered**:

- Compare title/version only: rejected as the existing defect.
- Compare path names only: rejected because schema and response drift would remain undetected.

---

## Alembic-Only Initialization

**Decision**: Keep Alembic revisions as the sole schema definition. Add a programmatic helper that
runs `upgrade head` on an existing SQLAlchemy connection via `connection.run_sync`. Application
startup, CLI paths, file-based tests, and shared in-memory integration tests all call this helper.
Remove `_SCHEMA_SQL`.

**Rationale**: Passing the existing connection is essential for SQLite `:memory:` because a second
connection may see a different database. It also avoids invoking `asyncio.run` inside the running
application event loop. One connection-aware path gives test and runtime databases identical
revision metadata and structure.

**Alternatives considered**:

- Invoke `alembic.command.upgrade` against a URL from async startup: rejected because Alembic's
  environment creates its own engine and cannot reliably share in-memory state with the running
  application.
- Keep embedded SQL for tests: rejected because it is the duplicate authority being removed.
- Create schema from SQLAlchemy declarative metadata: rejected because repositories intentionally
  use raw SQL without a declarative base.

---

## Legacy Database Reconciliation

**Decision**: Provide an explicit `qava db reconcile` command for databases with application
tables but no `alembic_version`. Introspect tables, columns, primary keys, foreign keys, unique
constraints, and indexes; stamp `0001_initial` only when they exactly match the expected initial
schema. Refuse partial or divergent schemas with a diagnostic. Normal startup never stamps
automatically.

**Rationale**: Running `0001_initial` over an old embedded-SQL database would attempt to recreate
tables, while blind stamping could bless an incompatible schema. Explicit verified reconciliation
is safe, testable, and appropriately rare.

**Alternatives considered**:

- `CREATE TABLE IF NOT EXISTS` inside migrations: rejected because it hides drift and weakens
  migration correctness guarantees.
- Automatically stamp any non-empty database at startup: rejected due to data integrity risk.
- Drop and recreate legacy databases: rejected because retained session and questionnaire data
  must survive unification.

---

## Draft Deletion

**Decision**: Add `AuthoringService.delete_draft`, delegate to the existing `DraftRepository`
delete operation, and make the route return 204 when a row was deleted or the shared 404 problem
response when the draft is unknown. The no-op read guard in the current route is removed.

**Rationale**: The repository operation already exists; the route currently performs only a read
and returns 204 unconditionally. The service method restores ownership consistency with other
authoring use cases and is the smallest correct change.

**Alternatives considered**:

- Inject the repository directly into the router: rejected because routers otherwise delegate all
  authoring operations and should not own persistence.
- Soft-delete with a deleted flag: rejected because drafts are mutable scratch state and hard
  delete is the correct semantic for the MVP.
