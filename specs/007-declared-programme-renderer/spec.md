# Feature Specification: Declared Programme Renderer

**Feature Branch**: `007-declared-programme-renderer`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Render declared grouped programme questions with ordinary typed controls, without coupling the custom-home domain into the Qava engine."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete a Declared Programme (Priority: P1)

A respondent completing a questionnaire that declares a grouped programme of selectable items can set the status of each relevant item and provide optional declared details through familiar labelled controls. They do not need to understand JSON or machine property names.

**Why this priority**: The checked-in programme question is already declared for a respondent-facing experience, but it currently falls back to an advanced JSON input because the generic structured form cannot interpret its grouped declaration.

**Independent Test**: Open a session containing a valid declared programme question, select statuses and optional details for items in multiple groups, submit the answer, and verify the result draft receives the declared typed object without presenting raw JSON.

**Acceptance Scenarios**:

1. **Given** a questionnaire declares item groups, permitted statuses, and respondent-facing labels, **When** a respondent opens the programme question, **Then** they see the grouped labelled items and permitted status controls instead of a raw JSON editor.
2. **Given** a respondent selects a status for an item, **When** they submit the answer, **Then** the submitted value retains the item's declared stable identifier and selected stable status value.
3. **Given** an item has declared optional details, **When** a respondent provides details, **Then** each detail retains its declared value shape and stable option values in the submitted answer.
4. **Given** the server accepts a programme answer, **When** the session is recalculated, **Then** the canonical result, health, and next eligible interaction update through the existing deterministic flow.

---

### User Story 2 - Publish Only Renderable Programme Declarations (Priority: P2)

An author receives a deterministic validation issue before publication when a declared programme is incomplete or incompatible with its declared answer shape. Respondents never encounter an accidental advanced-JSON downgrade for a programme declaration that appears complete.

**Why this priority**: Publication-time validation turns the renderer contract into an author-visible guarantee and prevents future definition packs from reproducing this failure.

**Independent Test**: Validate one complete programme declaration and variants missing required groups, stable item values, permitted statuses, or compatible detail declarations; only the complete declaration can be published.

**Acceptance Scenarios**:

1. **Given** an author declares a programme with complete groups, item identifiers, statuses, optional detail declarations, and a compatible answer definition, **When** the definition is validated, **Then** it remains publishable.
2. **Given** a programme declaration omits required rendering information or contradicts the answer definition, **When** the definition is validated, **Then** publication is blocked with a specific explanation of the invalid declaration.
3. **Given** an otherwise valid programme declaration, **When** it is published as a new version, **Then** existing published versions and sessions remain unchanged.

---

### User Story 3 - Reuse the Declared Programme Contract (Priority: P3)

An author of a future questionnaire can use the same declared programme component for grouped selectable items without adding domain-specific runtime behavior.

**Why this priority**: The immediate custom-home question establishes the first use case, while keeping the contract reusable protects Qava's domain-neutral runtime.

**Independent Test**: Render a second representative programme declaration with different labels, groups, identifiers, and statuses, and verify it produces its declared typed answer without custom questionnaire logic.

**Acceptance Scenarios**:

1. **Given** two questionnaires declare different valid programme content, **When** each is rendered, **Then** the same component behavior uses only their respective declarations.
2. **Given** a programme declaration changes display labels while preserving stable identifiers, **When** a respondent submits an answer, **Then** stored identifiers remain unchanged.

### Edge Cases

- A programme has no selected items: the submitted value follows the declared required and minimum-selection rules, and any validation feedback identifies the required action without discarding other entries.
- A declared item lacks a stable identifier, label, or valid status set: the author is blocked before publication with a declaration-specific issue.
- A declared detail control is unsupported or incompatible with its value definition: the author is blocked before publication; the respondent is not sent to a raw JSON fallback.
- A respondent changes an item's status after adding details: the retained or removed details follow the declaration's published rules and remain visible in the submitted typed answer.
- An existing session is pinned to an earlier published questionnaire version: it retains its prior component contract and answer history; new behavior is available only in a fresh session from a newly published version.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render a valid declared programme as grouped respondent-facing controls instead of raw JSON.
- **FR-002**: A programme declaration MUST provide stable identifiers and display labels for every selectable item.
- **FR-003**: The system MUST allow a respondent to select only statuses explicitly declared for an item programme and MUST retain the selected stable status values.
- **FR-004**: The system MUST render optional item details only when they are fully declared with supported control semantics, and MUST retain their declared typed values.
- **FR-005**: The system MUST emit a single typed object that conforms to the programme answer definition and can be mapped by the existing deterministic session flow.
- **FR-006**: The system MUST preserve the existing direct mapping target, server-side validation, result projection, health calculation, and interaction progression for an accepted programme answer.
- **FR-007**: The system MUST validate programme declarations before publication and MUST block publication when required groups, item identifiers, status values, detail declarations, or answer-definition compatibility are missing or invalid.
- **FR-008**: The system MUST show an explicit unsupported state for an invalid published programme contract and MUST NOT silently substitute an advanced JSON editor.
- **FR-009**: The programme component contract MUST be domain-neutral: runtime behavior MUST derive only from declared groups, item identifiers, labels, statuses, details, and answer definition.
- **FR-010**: The system MUST publish changed programme declarations as a new immutable questionnaire version and MUST NOT alter answers, component contracts, or version bindings of existing sessions.

### Constitution Alignment *(mandatory)*

- **Output Contract Impact**: The existing programme mapping target remains authoritative. The declared answer definition specifies the typed evidence that satisfies the corresponding output need; no destination fields or mappings are added.
- **Typed Interaction Impact**: The renderer consumes a published domain-neutral programme declaration and emits only declared stable item, status, and detail values. Labels remain presentation metadata and do not replace stored identifiers.
- **AI Policy Boundary**: This feature adds no AI behavior. Declaration validation and all respondent interactions have deterministic behavior whether assistance is available or not.
- **Projection and Health**: A server-accepted answer uses the existing recalculation path to refresh mappings, canonical result, provenance, health, attention items, and the next interaction. Invalid declarations do not create session answers.
- **Publication and Stability**: A programme declaration is validated before explicit publication. Published versions and their sessions are immutable; the corrected declaration requires a new published version and a new session for use.

### Key Entities *(include if feature involves data)*

- **Programme declaration**: Published presentation and compatibility metadata containing grouped selectable items, their stable identifiers and labels, permitted statuses, and optional item detail declarations.
- **Programme item**: One selectable declared item, identified by a stable value and presented with a respondent-facing label in a group.
- **Programme selection**: The typed evidence for one selected programme item, including its stable item identifier, selected status, and optional declared details.
- **Programme compatibility issue**: A deterministic publication-blocking issue explaining why a programme declaration cannot produce a compatible respondent interaction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid published programme declarations render grouped respondent-facing controls without presenting a raw JSON editor.
- **SC-002**: In a representative usability review with five non-technical participants, at least four can select an item status and add an optional declared detail without assistance or a JSON syntax error.
- **SC-003**: 100% of incomplete or incompatible programme declarations are rejected before publication with an issue that identifies the affected declaration element and reason.
- **SC-004**: 100% of accepted programme answers retain their declared stable item, status, and detail values in the canonical result at the existing mapping target.
- **SC-005**: Existing sessions pinned to earlier questionnaire versions retain their original answer history and component behavior in all compatibility checks.

## Assumptions

- The programme answer is represented as a typed collection of declared item selections within one object, so item details remain optional and associated with a stable item identifier.
- The checked-in custom-home programme declaration is the first consumer, but the component contract must be reusable by other questionnaire domains without runtime special cases.
- Native accessible status and detail controls are sufficient for the initial experience; item duplication, item reordering, free-form undeclared items, and unit conversion remain out of scope.
- The existing session answer endpoint, mapping behavior, result projection, health rules, and publication workflow remain unchanged.
- A malformed published declaration is surfaced as unsupported rather than being interpreted as an open-ended object, while genuinely unconstrained object questions retain their existing advanced JSON path.