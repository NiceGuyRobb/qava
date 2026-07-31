# Feature Specification: Qava MVP

**Feature Branch**: `001-qava-mvp`

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "Build the output-driven Q&A engine described in README.md."

## Clarifications

### Session 2026-07-25

- Q: What tenancy model must the MVP support? → A: Single-tenant deployment with trusted authors and respondents.
- Q: How should the MVP handle identity and authorization? → A: Host-provided identity with Qava role checks.
- Q: How long should sessions, interactions, assisted proposals, and publication records be retained? → A: Retain until explicit session deletion.
- Q: What concurrent interview load should the MVP support? → A: Up to 100 active sessions.
- Q: What should session deletion do to previously published destination artifacts? → A: Delete Qava records only; external artifacts remain.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce a Live Result from an Output Contract (Priority: P1)

As a questionnaire author, I provide a structured output contract, resolve any ambiguous authoring decisions, and publish an immutable questionnaire. As a respondent, I answer that questionnaire through compatible controls and see a typed result draft update after every accepted answer.

**Why this priority**: This is Qava's essential product loop. It proves that an output requirement can become a usable interview and continuously produce the requested artifact without questionnaire-specific client logic.

**Independent Test**: Supply a contract containing required scalar, choice, conditional, collection, and dynamically sourced values; publish the generated questionnaire; complete and edit answers in a generic client; verify that each accepted revision returns the next eligible interaction and a contract-valid partial result.

**Acceptance Scenarios**:

1. **Given** a valid output contract, **When** the author starts a draft, **Then** the system identifies addressable output needs and proposes typed questions, mappings, and compatible answer controls.
2. **Given** an authoring decision that is ambiguous or low-confidence, **When** the draft is reviewed, **Then** the system asks the author to confirm, override, or reject the proposal before publication.
3. **Given** a valid draft with all blocking decisions resolved, **When** the author publishes it, **Then** the system creates a self-contained immutable questionnaire version whose links, mappings, choices, controls, policies, and required output needs have passed publication validation.
4. **Given** a respondent starts a session against an exact questionnaire version, **When** the session view is returned, **Then** it contains progress, one eligible interaction, its answer contract and component specification, the current canonical result draft, health summary, readiness, and permitted actions.
5. **Given** a rendered question, **When** the respondent submits a schema-compatible value, **Then** the answer is accepted, mapped to its declared output location, the session revision advances, and the complete updated session view is returned.
6. **Given** a choice with a display label and stable machine identifier, **When** the respondent selects it, **Then** the label is displayed while the stable identifier is stored and projected.
7. **Given** an earlier accepted answer is edited, **When** the replacement is accepted, **Then** dependent applicability, mappings, projection, provenance, health, readiness, and the next eligible interaction are recalculated.
8. **Given** an interrupted session, **When** the respondent resumes it, **Then** the latest accepted answers, generated interactions, current result, and appropriate next interaction are restored for the same questionnaire version.

---

### User Story 2 - Improve the Interview with Bounded Assistance (Priority: P2)

As an author and respondent, I receive agent-assisted proposals, question ordering, rephrasing, and clarifications that improve the interview while all accepted values, mappings, and side effects remain governed by deterministic rules.

**Why this priority**: Bounded assistance differentiates Qava from a fixed form while preserving the correctness established by the core loop.

**Independent Test**: Run the same published questionnaire with valid assistance, unavailable assistance, malformed assistance, and a request outside policy; verify improved in-policy interactions when available and equivalent deterministic completion behavior otherwise.

**Acceptance Scenarios**:

1. **Given** an output need with multiple compatible authoring choices, **When** assistance proposes a question or control, **Then** the proposal identifies what it serves, provides confidence and reasons, and remains subject to deterministic compatibility validation and author resolution.
2. **Given** multiple eligible runtime interactions, **When** assistance is available, **Then** it may rank only that bounded eligible set using published policy and cannot create undeclared output needs.
3. **Given** ambiguous evidence that permits clarification, **When** assistance formulates a clarification, **Then** the interaction declares its requirement, accepted answer shape, reason, classification, and applicable policy limit.
4. **Given** unavailable, malformed, or out-of-policy assistance, **When** the interview continues, **Then** deterministic ordering selects a valid next interaction without corrupting or blocking an otherwise answerable session.
5. **Given** a proposed value extracted from free text, **When** policy requires confirmation, **Then** the value remains a proposal until it passes validation and the respondent confirms it.

---

### User Story 3 - Understand Readiness and Publish Explicitly (Priority: P3)

As a respondent or downstream operator, I can understand the fitness of every result revision, resolve concrete attention items, preview delivery, and explicitly publish an eligible revision with an auditable receipt.

**Why this priority**: A continuously projected result becomes operationally useful only when its quality is explainable and external side effects are deliberate and traceable.

**Independent Test**: Build a session through incomplete, invalid, attention-needed, ready, and published revisions; verify explainable health and gates at each revision, then publish an exact ready revision twice with the same idempotency identity and verify one durable outcome.

**Acceptance Scenarios**:

1. **Given** any accepted session revision, **When** health is evaluated, **Then** the user receives completeness, validity, confidence, consistency, and specificity scores plus a weighted headline score, readiness, evidence, and actionable attention items.
2. **Given** missing required output or a blocking validation failure, **When** publication readiness is evaluated, **Then** the revision remains in progress and the blocking causes are explicit regardless of its headline score.
3. **Given** a contract-valid revision whose configured publication gate passes, **When** the user reviews it, **Then** it is marked ready without being published automatically.
4. **Given** a ready revision, **When** an authorized user explicitly publishes through an allowed destination, **Then** the exact requested revision is validated, delivered once, marked published only after success, and associated with a durable receipt.
5. **Given** a repeated publication request with the same idempotency identity, **When** it is processed, **Then** it does not create a duplicate destination artifact and returns the existing outcome.
6. **Given** a failed publication attempt, **When** the failure is returned, **Then** the session result remains intact, the attempt is auditable, and no successful publication state is recorded.
7. **Given** a host-authenticated user without publisher permission, **When** the user requests publication, **Then** Qava rejects the action without invoking the destination and records the denied attempt as appropriate for audit.
8. **Given** a session with successful publications, **When** an authorized user requests session deletion, **Then** Qava warns that external artifacts will remain and deletes only its session-scoped records after confirmation.

---

### User Story 4 - Author Qava Questionnaires with Qava (Priority: P4)

As a questionnaire author, I can use a guided Qava interview to design and publish another questionnaire, while retaining a raw structured-document escape hatch for bulk edits.

**Why this priority**: Self-hosted authoring demonstrates that the engine's contracts, controls, projection, health, and publication model are general enough to administer the product itself.

**Independent Test**: Use the bootstrapped meta-questionnaire to create a questionnaire containing collections, cross-references, and live catalog choices; resolve its health issues; publish it to the registry; and run a session against the resulting version.

**Acceptance Scenarios**:

1. **Given** the published-questionnaire contract as the desired output, **When** an author completes the meta-questionnaire, **Then** the continuously projected result is a questionnaire draft governed by the same validation and health rules as any other output.
2. **Given** a question requiring variable numbers of questions or choices, **When** the author adds items, **Then** bounded nested collections capture typed arrays without free-text substitution.
3. **Given** a design choice sourced from the live component catalog, **When** options are presented, **Then** the author sees current labels and the result stores stable catalog identifiers.
4. **Given** a valid meta-questionnaire result, **When** the author explicitly publishes it, **Then** the registry creates a new immutable questionnaire version and returns its identity and version.
5. **Given** a raw questionnaire document, **When** an author submits it through the escape hatch, **Then** it passes the same publication gate and produces the same form of immutable version and receipt as guided authoring.

### Edge Cases

- An output contract is structurally invalid, contains an unsupported shape, or has no addressable output needs.
- Required output fields cannot be satisfied by the draft's declared questions and mappings.
- Duplicate identifiers, missing references, conflicting mappings, invalid conditions, or incompatible controls are present at publication time.
- A collection exceeds its configured nesting or item limits, or a dynamic option provider is unavailable.
- A renderer does not support the resolved component and no declared compatible fallback exists.
- A submitted answer has the wrong type, uses an unknown choice identifier, targets a stale interaction, or arrives after the answer became inapplicable.
- A question is skipped when skipping is prohibited, or a required question is skipped and therefore cannot satisfy readiness.
- Editing an answer makes later accepted answers inapplicable or introduces a contradiction.
- Two clients submit changes from the same prior revision.
- Assistance times out, returns malformed content, names undeclared identifiers, exceeds clarification limits, or requests a prohibited action.
- Health weights are missing or invalid, or supporting evidence for an agent-produced observation cannot be found.
- A publication request names a stale revision, fails destination validation, times out after an uncertain outcome, or repeats after success.
- A published questionnaire is edited or an existing session is asked to move to another version without an explicit migration.
- A session with interaction, assisted-proposal, and publication records is explicitly deleted.
- A session deletion follows a successful publication whose external artifact cannot be retracted by Qava.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a structured output contract that defines the canonical result's shape, required values, constraints, and accepted machine values.
- **FR-002**: The system MUST derive addressable output needs from the output contract and retain stable identifiers for references, evidence, health, and provenance.
- **FR-003**: The system MUST support draft authoring that proposes or records questions, answer constraints, stable choices, output mappings, applicability, presentation, health policy, and assistance policy.
- **FR-004**: The system MUST expose unresolved or low-confidence authoring decisions for author confirmation, override, or rejection and MUST prevent publication while blocking decisions remain.
- **FR-005**: The system MUST allow authors to override prompts, grouping, ordering preferences, compatible controls, weights, and assistance policy without application-code changes.
- **FR-006**: The system MUST validate questionnaire publication for unique identifiers, valid references and targets, compatible answer/control contracts, non-conflicting mappings, satisfiable required output, valid policies, and bounded permissions.
- **FR-007**: The system MUST publish a valid questionnaire as a self-contained immutable version and MUST keep existing sessions attached to their original version.
- **FR-008**: The system MUST resolve answer controls using author override first, deterministic inference when unambiguous, bounded recommendation when useful, author confirmation when unresolved, and a declared compatible fallback when permitted.
- **FR-009**: The system MUST support typed controls for boolean, single and multiple choice, short and long text, bounded numbers, monetary values, dates and times, structured addresses, durable file references, and bounded collections of typed items.
- **FR-010**: The system MUST support choices from both published static lists and named runtime providers while preserving stable stored identifiers separately from display labels.
- **FR-011**: The system MUST support bounded applicability conditions based on accepted answers using equality, containment, and existence checks and MUST recalculate applicability after answer changes.
- **FR-012**: The system MUST create a session against an exact questionnaire identity and version and return a complete renderable session view after every read or accepted mutation.
- **FR-013**: A session view MUST include session identity and revision, progress, the current interaction and accepted answer shape, a component specification, the canonical result draft, health and attention summary, readiness, and permitted actions.
- **FR-014**: The system MUST validate every submitted value against the interaction's accepted answer contract before storing or projecting it.
- **FR-015**: The system MUST distinguish the typed machine value used for projection from convenience display text and MUST preserve answer source and revision provenance.
- **FR-016**: The system MUST support direct mapping of an accepted answer to one declared output location and composition of declared answers into a typed object or collection.
- **FR-017**: The system MUST report mapping and validation failures as attention items without silently modifying or corrupting the canonical result.
- **FR-018**: After every accepted answer, edit, or permitted skip, the system MUST recalculate affected applicability, mappings, result projection, provenance, health, readiness, and next-interaction candidates.
- **FR-019**: The system MUST persist authoritative session state for resume and answer editing, while retaining append-only interaction records sufficient to explain questions shown, answers, clarifications, reviews, skips, and navigation.
- **FR-020**: The system MUST reject stale session mutations by comparing the submitter's expected revision with the authoritative revision.
- **FR-021**: The system MUST allow navigation to declared sections or unresolved output needs without requiring questionnaire-specific routing logic in the client.
- **FR-022**: The system MUST generate a deterministic eligible interaction set from unresolved required needs, invalid or conflicting answers, useful optional needs, permitted clarifications, and required reviews.
- **FR-023**: Bounded assistance MAY propose authoring metadata, rank eligible interactions, rephrase without changing meaning, formulate permitted clarifications, and propose normalized values, but MUST operate only on declared identifiers, contracts, and policy limits.
- **FR-024**: The system MUST validate all assisted output as untrusted structured input and MUST prevent assistance from fabricating answers, bypassing validation, mutating published contracts, creating destination fields, accessing undeclared tools or destinations, or publishing results.
- **FR-025**: Every assisted path MUST have deterministic fallback behavior that permits the core authoring or interview flow to continue when assistance is unavailable or invalid.
- **FR-026**: Runtime-generated interactions MUST record the output need served, accepted answer shape, compatible presentation, reason, classification, and applicable policy limit and MUST be retained for resume and audit.
- **FR-027**: The system MUST assess each result revision across completeness, validity, confidence, consistency, and specificity using published inspectable rules and configured weights.
- **FR-028**: Health MUST include dimension scores from 0 to 100, a weighted headline score, a readiness state, supporting evidence, and actionable attention items, and MUST NOT use the headline score as the sole publication criterion.
- **FR-029**: The system MUST classify a result as in progress while blocking requirements or validation errors remain, ready when its configured publication gate passes, and published only after confirmed delivery of a specific revision.
- **FR-030**: The system MUST provide a side-effect-free preview of the canonical result and destination validation outcome before publication.
- **FR-031**: Publication MUST require an explicit authorized action, validate the exact requested revision, be idempotent, and return an immutable receipt containing destination identity, revision, time, status, and an external reference when available.
- **FR-032**: The MVP MUST publish canonical structured documents through a JSON document destination and MUST isolate destination translation behind a common validate, preview, and publish contract.
- **FR-033**: The system MUST retain immutable publication attempts and receipts separately from current session state.
- **FR-034**: The system MUST provide one generic client capable of rendering the built-in semantic component catalog, submitting typed actions, and displaying progress, result preview, health, readiness, and errors without questionnaire-specific business logic.
- **FR-035**: Unsupported controls MUST fail explicitly or use a declared schema-compatible fallback and MUST NOT degrade typed values into arbitrary strings.
- **FR-036**: The system MUST support guided self-hosted questionnaire authoring in which the published-questionnaire contract drives a meta-questionnaire and successful publication registers a new immutable questionnaire version.
- **FR-037**: Self-hosted authoring MUST support bounded nested collections, dynamic component-catalog choices, cross-document validation surfaced as attention items, and raw structured-document submission through the same publication gate.
- **FR-038**: The MVP MUST exclude general workflow or graph execution, unrestricted autonomous agents, arbitrary code execution, runtime mutation of published contracts, drag-and-drop form design, collaborative editing, automatic version migration, continuous external writes after answers, and additional destination families before the canonical document path is proven.
- **FR-039**: The MVP MUST support a single-tenant deployment with trusted authors and respondents; organization-level tenant isolation and collaborative multi-tenant administration are out of scope.
- **FR-040**: The MVP MUST accept authenticated identity from its host environment and enforce Qava permissions for questionnaire authoring, interview participation, and result publication; Qava-managed credentials are out of scope.
- **FR-041**: The system MUST retain a session and its associated interactions, assisted proposals, and publication records until an authorized explicit session-deletion action removes them; automatic time-based retention is out of scope for the MVP.
- **FR-042**: Session deletion MUST remove only Qava's session-scoped records, MUST warn when successful publications exist, and MUST NOT delete or retract previously published destination artifacts.

### Constitution Alignment *(mandatory)*

- **Output Contract Impact**: The supplied output contract is the sole authority for canonical result shape, accepted values, mappings, validation, completion, readiness, and publication eligibility. Every question and interaction traces to an addressable output need.
- **Typed Interaction Impact**: Every interaction declares an accepted answer shape and schema-compatible semantic component. Renderers preserve stable machine identifiers and contain no questionnaire-specific mapping or decision logic.
- **AI Policy Boundary**: Assistance is limited to proposals, ranking, meaning-preserving rephrasing, bounded clarification, and validated extraction proposals. It cannot accept values, mutate contracts, invent fields, or publish; deterministic authoring and interview paths remain complete without it.
- **Projection and Health**: Every accepted revision recalculates the canonical result, provenance, applicability, five explainable health dimensions, readiness, and attention items. Failures remain visible and cannot silently corrupt the result.
- **Publication and Stability**: Questionnaire publication creates immutable versions; result publication is an explicit, authorized, idempotent action against an exact revision. Interactions, revisions, assisted proposals, and publication outcomes retain audit evidence sufficient for resume and explanation.

### Key Entities *(include if feature involves data)*

- **Output Contract**: The authoritative description of the desired artifact's shape, required values, constraints, and accepted machine values.
- **Output Need**: A stable, addressable requirement derived from the contract and used to connect questions, evidence, provenance, health, and readiness.
- **Questionnaire Draft**: Mutable authoring state containing proposed and confirmed questions, mappings, controls, policies, and unresolved decisions.
- **Published Questionnaire**: A self-contained immutable runtime package identified by questionnaire identity and version.
- **Question / Interaction**: A request for typed evidence bound to one or more output needs, an accepted answer shape, a reason, and a semantic component specification.
- **Component Catalog Entry**: A versioned semantic control definition with compatible answer shapes, accepted properties, capabilities, accessibility expectations, and fallback behavior.
- **Session**: The authoritative evolving state of one interview, including questionnaire version, accepted answers, current context, revision, lifecycle, and publication records.
- **Accepted Answer**: A validated typed machine value with display metadata, source, served output needs, and revision provenance.
- **Result Projection**: The revision-specific canonical structured artifact derived from accepted answers and declared mappings.
- **Health Assessment**: Revision-specific dimension scores, headline score, readiness, evidence, and attention items produced by published rules.
- **Interaction Record**: Append-only evidence of a shown question, submitted answer, clarification, review, skip, or navigation action.
- **Publication Receipt**: Immutable evidence of a destination attempt and outcome for an exact result revision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, authors can turn the representative custom-home output contract into a publishable questionnaire without writing questionnaire-specific application code.
- **SC-002**: All published test questionnaires pass 100% of identifier, reference, mapping, answer/control compatibility, required-output satisfiability, and policy-boundary checks before becoming available to sessions.
- **SC-003**: With up to 100 active sessions, at least 95% of accepted answers and edits return the complete updated session view and canonical result draft within 1 second, and 100% complete within 3 seconds.
- **SC-004**: A generic client successfully renders and captures valid machine values for every control family included in the MVP catalog, including collections and dynamically sourced choices, without questionnaire-specific code.
- **SC-005**: Across the acceptance suite, 100% of displayed choice labels project their corresponding stable machine identifiers rather than display text.
- **SC-006**: All supported answer edits produce the expected dependent applicability, projection, provenance, health, readiness, and next-interaction changes with no stale derived values.
- **SC-007**: Every assisted acceptance scenario can complete successfully when assistance is unavailable or returns invalid output, using deterministic fallback with no loss or corruption of accepted answers.
- **SC-008**: For every tested result revision, users can identify why it is not ready or needs attention from evidence-linked attention items without consulting internal logs or private model reasoning.
- **SC-009**: In Playwright acceptance testing, a first-time respondent can complete the representative questionnaire, review its live result, correct an answer, and identify publication readiness without domain-specific client instructions.
- **SC-010**: In concurrency testing, 100% of stale writes are rejected and no newer accepted answer is overwritten.
- **SC-011**: In publication testing, no destination artifact is produced without an explicit action, every successful action has a receipt tied to the exact revision, and repeated requests with the same idempotency identity produce no duplicates.
- **SC-012**: An author can create, validate, publish, and run a new questionnaire through the guided self-hosted authoring experience in 15 minutes or less for a representative five-question contract.
- **SC-013**: Audit review can trace 100% of projected output values in the acceptance suite to their supporting accepted answers and can trace every publication state to an immutable attempt or receipt.
- **SC-014**: The complete MVP demonstration covers the path from supplied output contract through questionnaire publication, typed interview, continuous result and health updates, answer editing, deterministic fallback, explicit publication, and durable receipt in one uninterrupted scenario.

## Assumptions

- The MVP serves trusted questionnaire authors, respondents, and authorized publication operators within one tenant; collaborative authoring, cross-tenant isolation, and fine-grained organizational permission models are outside this feature.
- JSON Schema Draft 2020-12 is the accepted MVP output-contract vocabulary, with documented Qava annotations only where presentation or policy cannot be expressed by the base contract.
- The canonical MVP result is a typed JSON document. Other destination formats translate that result in later features and do not alter session semantics.
- One built-in web component catalog and generic renderer are sufficient to prove renderer independence; native, terminal, and voice renderers are deferred.
- Direct and compose mappings are sufficient for the MVP. Named transforms and unconfirmed assisted extraction are deferred.
- Collection nesting and clarification generation are bounded by published policy; exact operational limits will be selected during planning and exposed clearly to authors.
- The host environment authenticates identities; Qava does not store or verify credentials and instead authorizes authoring, interview, and publication capabilities from the supplied identity context.
- The MVP has no scheduled retention service; an authorized explicit session deletion is the lifecycle boundary for session-scoped audit records.
- The MVP capacity target is 100 concurrently active interview sessions within one tenant; larger-scale operation is deferred.
- Standard accessibility expectations apply to the built-in renderer and component catalog, including keyboard operation, programmatic labels, error association, and non-color-only status communication.
- Session snapshots are authoritative current state; append-only interaction records provide audit explanation without requiring full event sourcing.
- Existing sessions do not migrate automatically when a new questionnaire version is published.
- Private model reasoning is neither required nor retained; structured recommendations, reasons, evidence, model identity, and policy version are retained when needed for audit.
- The questionnaire registry and canonical JSON document destination are the only publication destinations required for this MVP.
