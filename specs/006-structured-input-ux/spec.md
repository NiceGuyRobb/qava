# Feature Specification: Structured Input UX

**Feature Branch**: `006-structured-input-ux`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Improve the structured-input experience so ordinary respondents do not encounter a JSON editor when a questionnaire has enough declared information to render familiar controls. Evaluate requested enhancements by value relative to effort and exclude fringe-value work."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Structured Answers Without JSON (Priority: P1)

A respondent completing an existing questionnaire encounters labeled, familiar controls for every declared field in a structured object or repeated item, including fields that allow multiple selections and measurements. They can submit the same typed answer shape without understanding JSON syntax or internal property names.

**Why this priority**: This removes the current primary usability failure from questions already present in the shipped definition pack. It has direct value for every non-technical respondent and preserves the established output contract.

**Independent Test**: Open each existing structured and repeatable question that declares fields, complete all available field types, and verify that no raw JSON editor appears and the accepted answer retains the declared stable values and structure.

**Acceptance Scenarios**:

1. **Given** a structured question declares a multiple-choice field, **When** a respondent chooses one or more options, **Then** they use a visible multi-choice control and the answer retains the selected stable values in the field's array.
2. **Given** a structured question declares a measurement field with allowed units, **When** a respondent enters a measurement, **Then** they can provide the value and unit through separate labeled controls and the answer retains the declared measurement structure.
3. **Given** a repeatable question declares labeled fields for each item, **When** a respondent adds or edits an item, **Then** they use labeled controls for those fields rather than a raw JSON editor.
4. **Given** a respondent submits a completed structured answer, **When** the answer is accepted, **Then** the canonical result, health, and next eligible interaction update through the existing deterministic session flow.

---

### User Story 2 - Use Raw JSON Only Deliberately (Priority: P1)

A respondent sees raw JSON only when the question is genuinely open-ended and has no complete declared field experience. The fallback is clearly identified as an advanced option, while users who can use the normal form are never silently sent to it because one declared field is unsupported.

**Why this priority**: Removing accidental fallback is essential to making the primary interview usable. Retaining a deliberate advanced path preserves capability for genuinely unconstrained authoring scenarios without making it the ordinary respondent experience.

**Independent Test**: Compare a fully declared structured question with an unconstrained structured question; the former renders standard controls while the latter explicitly identifies the advanced raw-JSON mode and preserves type validation.

**Acceptance Scenarios**:

1. **Given** a structured question has complete supported field declarations, **When** it is rendered, **Then** the respondent is not shown a raw JSON editor.
2. **Given** a structured question has no usable field declarations, **When** it is rendered, **Then** the raw JSON path is visibly labeled as advanced and gives a clear validation message for invalid structure.
3. **Given** a field declaration cannot be rendered, **When** the questionnaire is prepared for use, **Then** the issue is surfaced to an author instead of silently changing the respondent experience to raw JSON.

---

### User Story 3 - Author Predictable Structured Questions (Priority: P2)

An author defining a structured or repeatable question can declare the field labels, supported control kind, options, help text, examples, grouping, and item labels needed for a respondent-friendly form. Invalid or incompatible declarations are identified before the questionnaire is published.

**Why this priority**: Authoring safeguards prevent recurrence and make the user-facing form intentional. The highest-value portion is validation of currently supported controls; richer descriptive presentation can be adopted incrementally.

**Independent Test**: Create a draft with a compatible structured-field declaration and one with an unsupported or incomplete declaration; the valid draft remains publishable while the invalid draft identifies the specific field that must be corrected.

**Acceptance Scenarios**:

1. **Given** an author declares supported structured fields with human-readable labels and options, **When** the definition is validated, **Then** it is accepted and those labels and options are available to the respondent form.
2. **Given** an author declares a field component that is incompatible with the expected answer shape, **When** the definition is validated, **Then** publication is blocked with a field-specific explanation.
3. **Given** an author supplies optional help text or an example for a supported field, **When** the respondent views that field, **Then** the supplemental guidance is available without exposing machine identifiers.

### Value and Effort Decisions

| Requested capability | Evidence of value | Relative effort and risk | Scope decision |
| --- | --- | --- | --- |
| Multiple-choice fields inside structured and repeated answers | Existing household, garage, and structure questions already declare them; their absence can trigger the JSON fallback. | Low to medium; one reusable typed control and answer propagation path. | Include in P1. |
| Measurement fields inside structured answers | An existing home-structure question declares one; its absence can trigger the JSON fallback. | Medium; requires a stable value-and-unit answer experience and validation compatibility. | Include in P1. |
| Preserve existing nested objects and repeatable collections | Existing schemas can contain nested structures, and respondents need a form rather than JSON when fields are fully declared. | Medium; constrain work to already declared, supported field shapes. | Include only as compatibility coverage in P1; do not add a new general-purpose editor. |
| Author-supplied labels, item labels, help text, examples, and grouping | Labels and item labels directly improve comprehension; help and examples resolve common ambiguity. | Low for declared text; medium for presentation consistency. | Include validation and support in P2, with labels and item labels required where needed for meaningful rendering. |
| Validate structured component declarations before publication | Prevents a silent runtime downgrade to JSON and protects future questionnaires. | Medium; shared authoring validation and focused contract coverage. | Include in P2 after the P1 renderer path works. |
| Explicit advanced raw-JSON fallback | Retains capability for genuinely open-ended structures without imposing it on ordinary users. | Low; presentation and clear validation behavior. | Include in P1. |
| Duplicate collection item action | No current questionnaire evidence that duplication is a frequent respondent task. | Medium; must define copied values and avoid accidental duplicate mapped output. | Defer. |
| Reorder collection item action | No current requirement relies on collection order; order semantics may affect mappings or downstream interpretation. | High; needs explicit ordering semantics, keyboard operation, and accessibility design. | Defer until a definition pack establishes a user need and order contract. |
| Chip-style multiple choice as an alternative to checkboxes | Visual preference alone does not change completion capability. | Medium; requires accessible keyboard, focus, and small-screen behavior. | Defer; prioritize one accessible multi-choice control first. |

### Edge Cases

- A declared field is unsupported or incompatible with its expected answer shape: the author receives a field-specific validation issue; the respondent is not silently downgraded to raw JSON for an otherwise declared form.
- A structured answer contains a nested object or collection whose fields are incomplete: the form presents supported declared portions only when the entire submitted answer remains valid; otherwise the author must complete the declaration or use the explicit advanced mode.
- A respondent deselects all values in an optional multiple-choice field: the submitted value follows the declared empty-value rules and validation explains any required selection.
- A respondent enters an invalid measurement value or omits its required unit: the form identifies the specific missing or invalid portion without losing other entered values.
- A previously published questionnaire uses the earlier behavior: its version and active sessions remain stable; improved definitions and rendering behavior apply without altering accepted historic answers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render each fully declared structured object or repeated item with respondent-facing labeled controls rather than a raw JSON editor.
- **FR-002**: The system MUST support a multiple-choice field within a structured object or repeated item, allowing a respondent to select zero, one, or many declared options as permitted by the answer definition.
- **FR-003**: The system MUST support a measurement field within a structured object, allowing a respondent to enter a numeric value and select a declared unit while preserving the declared answer shape and stable values.
- **FR-004**: The system MUST preserve nested object and repeated-collection answers when their declared field shapes are supported, including add and remove actions already needed to complete a collection.
- **FR-005**: The system MUST keep raw JSON entry available only for an open-ended structured answer that lacks a complete supported field declaration, and MUST identify that path as an advanced mode.
- **FR-006**: The system MUST provide clear, field-specific validation feedback for invalid structured values without discarding a respondent's other valid entries.
- **FR-007**: The system MUST allow authors to declare respondent-facing labels, item labels, supported control kinds, options, and optional help text or examples for structured fields.
- **FR-008**: The system MUST validate structured and repeatable field declarations before publication and block publication when a declaration cannot be rendered compatibly with its expected answer shape.
- **FR-009**: The system MUST preserve existing stable machine values, answer schemas, mappings, and server-side answer validation for all structured answers.
- **FR-010**: The system MUST not add duplicate-item or reorder-item actions in this feature; those actions require a future documented user need and explicit collection-order semantics.

### Constitution Alignment *(mandatory)*

- **Output Contract Impact**: No output contract targets or mappings change. Structured controls capture existing declared shapes and stable values, and authoring validation prevents a presentation declaration from contradicting the expected answer shape.
- **Typed Interaction Impact**: Structured and repeated controls must emit the same typed values expected by the declared answer schema. Human-readable labels, help, and examples remain presentation metadata and never replace stored identifiers.
- **AI Policy Boundary**: This feature adds no AI judgment or authority. All component compatibility, accepted values, and fallback behavior remain deterministic whether assistance is available or not.
- **Projection and Health**: An accepted structured answer continues to trigger the existing deterministic recalculation of mappings, canonical result, provenance, health, attention items, and next interaction. Field validation failures remain inspectable and do not modify the result.
- **Publication and Stability**: Published questionnaires and pinned sessions remain immutable. Improved authoring declarations are introduced through a new draft and published version; the feature creates no external side effects or publication changes.

### Key Entities *(include if feature involves data)*

- **Structured field declaration**: Author-provided presentation and compatibility information for one property of an object or one property of an item in a repeated collection.
- **Structured answer**: A typed object or collection value submitted by a respondent and evaluated against its declared answer definition.
- **Advanced raw-JSON mode**: The explicit fallback input path for a genuinely open-ended structured answer that lacks a complete supported field declaration.
- **Component compatibility issue**: A field-specific authoring validation issue that explains why a declared structured field cannot be rendered or accepted safely.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of existing structured and repeated questions with complete supported declarations can be completed without entering raw JSON.
- **SC-002**: In usability testing with five non-technical participants, at least four complete a representative structured question containing multiple-choice or measurement data without assistance and without a JSON syntax error.
- **SC-003**: 100% of incompatible structured-field declarations are identified before publication with the affected field and reason shown to the author.
- **SC-004**: All accepted structured answers retain their declared value shape and produce the same canonical result updates as the equivalent valid answer submitted before this feature.
- **SC-005**: A respondent can identify the raw-JSON path as advanced, and can distinguish it from the default structured form, in 100% of reviewed open-ended structured-answer screens.

## Assumptions

- The current definition pack's existing field declarations are the primary evidence for P1 component support; support for unrepresented control kinds will be proposed only when a future definition pack demonstrates a respondent need.
- A checkbox-style accessible multiple-choice control is the initial default; chip styling is a presentation enhancement, not a separate functional requirement.
- Add and remove actions remain sufficient for the first release because no current questionnaire requires item duplication or ordering as meaningful respondent behavior.
- Measurement values and units will use the shapes already declared by the questionnaire's answer definitions; this feature does not invent or transform domain values.
- Existing published questionnaire versions and session answers remain unchanged; definition-pack improvements are published as a new version.