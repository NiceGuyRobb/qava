# Feature Specification: README Gap Closure

**Feature Branch**: `004-readme-gap-closure`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "Convert the README ↔ implementation gap analysis into a delivery spec that sequences closing the highest-value gaps while preserving the working deterministic core."

## Clarifications

### Session 2026-07-26

- Q: Which slices are in scope for this feature, and how is the agent layer handled? → A: Deliver US1–US5 fully; include US6 as stub/mock only — pure interfaces and hardcoded (fixture) responses with deterministic fallback, no real AI implementation.
- Q: What is the JSON document adapter's publish side effect? → A: Persist the canonical result as an immutable published-artifact record in Qava's own store; the receipt carries an internal reference.
- Q: Which dynamic option source providers must the MVP support? → A: A loosely coupled provider-registry seam with one initial provider (the component catalog); additional providers can be registered later without changing consumers.
- Q: How much bespoke authoring UI should this feature build? → A: None bespoke; US4 delivers the backend confirm/override/reject workflow plus a raw JSON path, and the guided authoring experience is delivered by US5's meta-questionnaire rendered through the existing runtime client (a questionnaire that builds a questionnaire).
- Q: What is the source of the rule-based health dimensions? → A: A fixed, built-in, published, inspectable rule set with no author configuration and no per-questionnaire defaults.

## User Scenarios & Testing *(mandatory)*

Each user story is one independently deliverable slice drawn from the verified gap analysis. Stories are ordered by value-per-effort and by dependency: earlier stories unlock later ones. Every story keeps the proven contract → question → answer → projection → health loop working end to end.

### User Story 1 - Complete the Typed Capture Loop (Priority: P1)

As a questionnaire author and respondent, I can author and answer questionnaires that use runtime-sourced option lists, deeper item collections, and every catalogued answer control, so the Phase 1 capture loop is complete and self-hosting prerequisites exist.

**Why this priority**: The capture loop is the product's foundation, and three known gaps (dynamic option sources, collection depth, and unmapped money/date controls) block both MVP acceptance and every later slice that depends on richer questionnaires.

**Independent Test**: Publish a questionnaire whose choices are drawn from a named runtime provider, whose answers include a nested collection of typed items, and whose questions include monetary and date/time values; complete it in the generic client and confirm each control renders, each stable value is stored, and the projection reflects every answer.

**Acceptance Scenarios**:

1. **Given** a question whose choices come from a named system provider, **When** the questionnaire is published and answered, **Then** the runtime supplies the current option set while storing the stable choice identifier rather than a display label.
2. **Given** a collection whose items themselves contain a nested collection, **When** items are added within the declared depth and item limits, **Then** each item field resolves its own control and the projection stores an array of typed objects.
3. **Given** a monetary answer and a date/time answer, **When** the question is rendered, **Then** the client selects the money and date/time controls from the catalog and stores typed values (amount with currency, ISO date/timestamp).
4. **Given** a collection or dynamic-option answer is edited, **When** the change is accepted, **Then** dependent applicability, mappings, projection, provenance, health, and the next interaction are recalculated consistently.

---

### User Story 2 - Publish a Result Through an Explicit Adapter (Priority: P2)

As a publisher, I can preview a ready result, then explicitly publish the exact session revision through a JSON document adapter and receive a durable receipt, so a completed interview produces a delivered artifact.

**Why this priority**: Publication is a core MVP acceptance criterion that is entirely unwired today; it converts a validated draft into the usable output that justifies the whole engine.

**Independent Test**: Take a session to a ready state, request a preview, publish the named revision through the JSON document adapter, and confirm a receipt is returned; repeat the same publication with the same idempotency key and confirm no duplicate side effect occurs.

**Acceptance Scenarios**:

1. **Given** a session at a ready revision, **When** a preview is requested, **Then** the canonical result is returned without any external side effect.
2. **Given** a ready revision and a configured JSON document adapter, **When** publication is requested with an expected revision, **Then** the configured gate is validated, the adapter is invoked, and a receipt with adapter identity, destination, revision, timestamp, status, and external reference is recorded and returned.
3. **Given** a revision that fails the publication gate, **When** publication is requested, **Then** the request is rejected with explicit blocking reasons and no artifact is delivered.
4. **Given** a publication that already succeeded for an idempotency key, **When** the same publication is requested again, **Then** the prior receipt is returned and no duplicate side effect occurs.
5. **Given** a stale expected revision, **When** publication is requested, **Then** the request is rejected without delivering an artifact.
6. **Given** a publication whose adapter outcome is indeterminate, **When** the attempt is recorded, **Then** the receipt is marked `outcome_unknown` and can be reconciled to a terminal status on a subsequent explicit check without creating a duplicate artifact.

---

### User Story 3 - Trust Explainable Health (Priority: P3)

As a respondent or reviewer, I can rely on each health dimension because its score comes from published, inspectable rules rather than placeholder heuristics, so readiness decisions are trustworthy.

**Why this priority**: Health already exists structurally, but confidence, consistency, and specificity are placeholder values; making them rule-based is required for readiness and publication gates to be defensible.

**Independent Test**: Construct sessions that exercise weak evidence, contradictory values, and imprecise-but-present values, and confirm the corresponding dimension scores change according to declared rules and produce concrete attention items.

**Acceptance Scenarios**:

1. **Given** answers with differing evidence strength, **When** health is assessed, **Then** the confidence dimension reflects declared rules and cites supporting evidence rather than a fixed heuristic.
2. **Given** two related values that contradict each other, **When** health is assessed, **Then** the consistency dimension drops and a concrete attention item identifies the conflict.
3. **Given** a value that is present but imprecise for its intended use, **When** health is assessed, **Then** the specificity dimension reflects the imprecision with a recommended action.
4. **Given** a result targeting an adapter with a validation gate, **When** health is assessed, **Then** validity may include a dry run so blocking structural errors surface as attention items before publication is attempted.

---

### User Story 4 - Author Without Writing Code (Priority: P4)

As an author, I can resolve ambiguous authoring decisions through explicit confirm/override/reject choices and edit questionnaires through a raw JSON path that passes the same publication gate, so authoring is self-service through the backend workflow. The guided, interactive authoring experience is delivered by US5's meta-questionnaire (rendered by the existing runtime client), so this slice builds no bespoke authoring UI.

**Why this priority**: Authoring exists only as an API with no explicit decision workflow; the decision workflow and raw JSON path are required before Qava can host its own builder as a meta-questionnaire.

**Independent Test**: Start a draft that surfaces at least one ambiguous decision, resolve it by confirming and by overriding through the backend workflow, publish, then make a bulk edit through the raw JSON path and confirm both routes converge on identical publication validation.

**Acceptance Scenarios**:

1. **Given** a draft with an ambiguous or low-confidence decision, **When** the author reviews it, **Then** the decision is presented for explicit confirm, override, or reject before publication is allowed.
2. **Given** an author override of a control or mapping, **When** the draft is revalidated, **Then** the override is preserved and validated for compatibility with the answer schema.
3. **Given** a bulk edit submitted as raw questionnaire JSON, **When** it is published, **Then** it passes the same publication gate as the guided path, and cross-document reference issues appear as attention items.
4. **Given** a draft with unresolved blocking decisions, **When** publication is attempted, **Then** publication is refused until every blocking decision is resolved.

---

### User Story 5 - Qava Authors Qava (Priority: P5)

As a platform owner, I can edit and publish questionnaires through a bootstrapped meta-questionnaire and a registry adapter, so the builder itself runs on the engine and the guided authoring experience is a questionnaire that builds a questionnaire, rendered by the existing runtime client with no bespoke builder UI.

**Why this priority**: Self-hosted authoring is the README's administration model and provides the guided authoring UI by reuse; it depends on collections, dynamic option sources, publication, and the authoring decision workflow from earlier slices, so it must follow them.

**Independent Test**: Load the bootstrapped meta-questionnaire, answer it to design a new questionnaire, publish through the registry adapter, and confirm the result is registered as a new immutable questionnaire version returned as an identity and version receipt.

**Acceptance Scenarios**:

1. **Given** the published-questionnaire schema used as a meta output contract, **When** the meta-questionnaire is answered, **Then** the result projection is a valid questionnaire document.
2. **Given** a completed meta interview, **When** it is published through the registry adapter, **Then** the questionnaire is written to the published-questionnaire store as a new immutable version and a receipt of identity and version is returned.
3. **Given** an edit to an existing questionnaire (including the meta-questionnaire), **When** it is republished, **Then** a new version is created and existing sessions remain attached to their original version.

---

### User Story 6 - Bounded Agent Assistance Seam (Stub/Mock) (Priority: P6)

As a platform owner, I can see the bounded-agent capability accounted for as a fully declared interface backed by hardcoded fixture responses, so the assistance seam, policy boundary, and deterministic fallback are proven without any real AI implementation.

**Why this priority**: The agent layer is the largest aspiration gap but the least urgent; scoping it to interfaces plus fixture responses reserves the seam and validates the policy and fallback contract while deferring real model integration to a future feature.

**Independent Test**: With assistance in fixture mode, confirm each declared operation (component recommendation, next-question ranking, question and clarification formulation, extraction) returns its hardcoded proposal, is validated by the engine, and is rejected or accepted per policy; then disable fixture mode and confirm every path still completes deterministically with identical correctness guarantees.

**Acceptance Scenarios**:

1. **Given** the assistance interface in fixture mode, **When** an authoring or runtime decision has room for judgment, **Then** a hardcoded proposal with confidence and reasons is returned through the declared interface and validated by the engine before use.
2. **Given** a fixture proposal that fails schema, compatibility, or policy checks, **When** it is evaluated, **Then** it is rejected and the deterministic decision is used instead.
3. **Given** assistance is disabled or a fixture is absent, **When** any assisted path runs, **Then** deterministic fallback completes the interview without corrupting output.
4. **Given** a fixture proposal is applied, **When** it enters the record, **Then** placeholder model identity, policy version, and supporting evidence are retained for audit, and extraction proposals require confirmation when policy demands it.
5. **Given** the assistance interface, **When** real AI implementation is later added, **Then** it can replace the fixture provider behind the same interface without changing engine or client contracts.

---

### Edge Cases

- A dynamic option provider is unavailable or returns an empty set at runtime.
- A nested collection exceeds declared depth or item limits.
- A money answer omits currency, or a date answer is out of an allowed range.
- A publication adapter is invoked but its outcome is unknown (partial success), requiring a resolvable receipt state.
- Two publish requests race with the same idempotency key at the same revision.
- A rule-based health dimension has insufficient evidence to score confidently.
- An author override conflicts with a later contract change during drafting.
- The meta-questionnaire is edited into a state that would fail its own publication gate.
- Assistance is enabled but partially configured, so only some operations are available.

## Requirements *(mandatory)*

### Functional Requirements

**Typed capture completion (US1)**

- **FR-001**: System MUST allow a question to source its choices from a named runtime provider resolved through a loosely coupled provider-registry seam, with the component catalog as the initial registered provider and additional providers registerable later without changing question, projection, or client contracts, while storing a stable choice identifier.
- **FR-002**: System MUST support nested item collections within declared depth and item limits, resolving each item field's control through the same inference rules, and the generic client MUST render nested collections recursively without questionnaire-specific logic.
- **FR-003**: System MUST support per-item mapping so collection answers project as arrays of typed objects.
- **FR-004**: System MUST make every catalogued answer control selectable, including monetary and date/time controls, and store their typed values.

**Publication (US2)**

- **FR-005**: System MUST provide a side-effect-free preview of the canonical result for a requested revision.
- **FR-006**: System MUST publish a named session revision only through an explicit action that first passes the configured publication gate.
- **FR-007**: System MUST deliver publication through a JSON document adapter that persists the canonical result as an immutable published-artifact record in Qava's own store, and record a durable receipt containing adapter identity, destination, revision, timestamp, status, and an internal external reference to the stored artifact.
- **FR-008**: System MUST make publication idempotent by returning the prior receipt for a repeated idempotency key without producing a duplicate side effect.
- **FR-009**: System MUST reject publication when the expected revision is stale or the gate fails, without delivering an artifact.
- **FR-027**: System MUST represent an indeterminate adapter outcome as a resolvable `outcome_unknown` receipt state and provide an explicit reconciliation path that resolves it to a terminal status without producing a duplicate artifact.

**Explainable health (US3)**

- **FR-010**: System MUST score each health dimension from a fixed, built-in, published, inspectable rule set that is not author-configurable, replacing the current placeholder values; author-configured headline weights and readiness gates remain in force and combine these fixed per-dimension scores.
- **FR-011**: System MUST produce concrete attention items with recommended actions for weak evidence, contradictions, and imprecise values.
- **FR-012**: System MUST allow validity to include an adapter validation dry run so blocking structural errors surface before publication.

**Self-service authoring (US4)**

- **FR-013**: System MUST surface ambiguous or low-confidence authoring decisions for explicit confirm, override, or reject before publication.
- **FR-014**: System MUST preserve and validate author overrides for compatibility with the answer schema and mappings.
- **FR-015**: System MUST accept a raw questionnaire JSON edit path that passes the identical publication gate as the meta-questionnaire (guided) path.
- **FR-016**: System MUST refuse publication while any blocking authoring decision remains unresolved.

**Self-hosted authoring (US5)**

- **FR-017**: System MUST treat the published-questionnaire schema as a meta output contract whose result projection is a valid questionnaire document.
- **FR-018**: System MUST provide a registry adapter whose publish step registers the result as a new immutable questionnaire version and returns an identity-and-version receipt.
- **FR-019**: System MUST allow any questionnaire, including the meta-questionnaire, to be edited and republished as a new version while existing sessions remain on their original version.

**Bounded agent assistance seam — stub/mock only (US6)**

- **FR-020**: System MUST declare a complete assistance interface for component recommendation, next-question ranking, question and clarification formulation, and value extraction, without implementing any real AI provider.
- **FR-021**: System MUST back the assistance interface with hardcoded fixture responses and validate every fixture proposal against schema, compatibility, and policy before use, rejecting invalid proposals.
- **FR-022**: System MUST provide a deterministic fallback that completes any assisted path when assistance is disabled or a fixture is absent.
- **FR-023**: System MUST retain placeholder agent audit metadata (model identity, policy version, supporting evidence), require confirmation for extraction when policy demands it, and allow a real AI provider to replace the fixture behind the same interface without changing engine or client contracts.

**Cross-cutting**

- **FR-024**: System MUST preserve the renderer-neutral client contract so no questionnaire-specific logic leaks into any client while these capabilities are added.
- **FR-025**: System MUST recalculate applicability, mappings, projection, provenance, health, readiness, and the next interaction after every accepted answer or edit across all new capabilities.
- **FR-026**: System MUST keep each slice independently deliverable without regressing the existing deterministic interview loop.

### Constitution Alignment *(mandatory)*

- **Output Contract Impact**: Every new capability continues to trace to declared output needs; dynamic options, collections, publication gates, and the meta output contract all preserve the output contract as the single source of truth for shape, accepted values, and readiness.
- **Typed Interaction Impact**: New controls (money, date/time, dynamic options, nested collections) preserve typed answer schemas and stable machine values, and renderers remain domain-neutral with no questionnaire-specific logic.
- **AI Policy Boundary**: Agent assistance is confined to proposals that the engine validates; AI never mutates contracts, accepts unvalidated values, or causes publication, and every assisted path has a deterministic fallback.
- **Projection and Health**: All slices recalculate projection, provenance, and health after each accepted answer; health becomes fully rule-based and explainable, with adapter dry-run validity surfacing blocking issues as attention items.
- **Publication and Stability**: Publication remains an explicit, gated, idempotent action producing durable receipts; published questionnaires and the meta-questionnaire remain immutable and versioned, and sessions stay resumable and auditable.

### Key Entities *(include if feature involves data)*

- **Dynamic Option Source**: A named runtime provider of choice options that yields stable identifiers and display labels only known at runtime.
- **Collection Item Schema**: The typed shape of a repeatable item, resolvable recursively within declared depth and item limits.
- **Publication Attempt & Receipt**: An explicit, idempotent delivery attempt and its durable outcome, including adapter identity, destination, revision, status (including a resolvable `outcome_unknown` state), and external reference.
- **Output Adapter**: A destination implementation exposing validate, preview, and publish, beginning with JSON document and registry adapters.
- **Health Dimension Rule**: The fixed, built-in, published, inspectable rule set (not author-configurable) that scores completeness, validity, confidence, consistency, and specificity and produces attention items; author-configured weights and readiness gates combine these scores.
- **Authoring Decision**: An ambiguous or low-confidence draft decision that requires explicit author confirm, override, or reject before publication.
- **Meta Questionnaire**: A questionnaire whose output contract is the published-questionnaire schema and whose publication registers a new questionnaire version.
- **Assistance Proposal**: A validated AI proposal (component, ranking, question, clarification, or extraction) with confidence, reasons, and retained audit metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of catalogued answer controls, including money and date/time, are selectable and render valid typed values in the generic client.
- **SC-002**: A respondent can complete a questionnaire that uses a runtime-sourced option list and a nested collection with every stored value being a stable typed value rather than a display label.
- **SC-003**: 100% of successful publications return a durable receipt, and a repeated idempotency key produces zero duplicate side effects.
- **SC-004**: Every health dimension changes only in response to declared rules, verified by targeted scenarios for weak evidence, contradiction, and imprecision.
- **SC-005**: A questionnaire can be authored, ambiguity resolved, and published through both the guided and raw JSON paths with identical gate results.
- **SC-006**: A new questionnaire version can be produced end to end through the bootstrapped meta-questionnaire and registry adapter.
- **SC-007**: With assistance disabled or failing, 100% of interviews and authoring flows still complete deterministically with unchanged correctness guarantees.
- **SC-008**: No slice regresses the existing deterministic interview loop, confirmed by the existing contract and integration checks remaining green.

## Assumptions

- The existing deterministic core (contract, questions, projection, sessions, concurrency) remains the baseline and is extended incrementally rather than replaced.
- Slices are delivered in priority order because later slices depend on capabilities earlier slices provide.
- The JSON document adapter is the first and only destination adapter proven before any Phase 4 ecosystem adapters are considered.
- Existing single-tenant identity, role checks, retention, and versioning rules from prior specs remain in force.
- Agent assistance is introduced as interface plus hardcoded fixture responses behind the already-defined disabled/fixture policy and stubbed repositories; no real AI provider is implemented in this feature, and real model integration is deferred to a future feature.
- Storage scaffolding that already exists for publications and assistance is reused rather than redesigned.
