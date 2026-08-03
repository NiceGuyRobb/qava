# Research: Declared Programme Renderer

## Decisions

1. **Use a domain-neutral `declared_programme` component.** Replace the custom-home source-pack
   use of `room_programme` with a generic component name and declaration vocabulary. The runtime
   derives behavior solely from groups, stable item values, labels, statuses, details, and the
   answer schema.
2. **Use a `selections` array within one typed object.** Each selection has `item_id`, `status`,
   and optional `details`. This keeps details attached to a stable item without using display text
   as an object key or giving group layout metadata semantic meaning.
3. **Separate stable values from display labels.** Groups, items, statuses, and select detail
   options use `{ value, label }` declarations. Renderers display labels and emit only values.
4. **Build a dedicated renderer.** `StructuredForm` correctly reserves its Advanced JSON fallback
   for open-ended objects, but it cannot express a fixed grouped item catalogue. Add a focused
   `DeclaredProgramme.vue` rather than extending generic descriptor recursion with programme
   semantics.
5. **Keep server runtime behavior unchanged.** The existing answer schema validator, direct
   mapping, evaluation, projection, health, session revision, and API response transport already
   carry a typed object unchanged. No endpoint, OpenAPI, persistence, or migration change is
   required.
6. **Validate declarations at existing publication gates.** Tighten the catalog props schema and
   add semantic programme compatibility checks to `validate_publication`. This shared path covers
   guided draft updates, raw replacement, and final publication.
7. **Treat malformed published programme contracts as unsupported.** A declared programme that
   cannot derive valid renderer props must render the existing explicit unsupported state, not be
   interpreted as a genuinely unconstrained object and sent to Advanced JSON.
8. **Prevent duplicate item selections deterministically.** JSON Schema cannot enforce uniqueness
   of an object property within array entries. Add a generic programme-answer rule that rejects
   repeated `item_id` values after schema validation.

## Findings

- Current fallback cause: `room_programme` is routed to `StructuredForm`, whose `fields` derivation
  only understands ordinary `fields` declarations or schema properties. The checked-in programme
  instead provides `groups`, `statuses`, and `item_details`, producing `fields: []` and the
  deliberate Advanced JSON fallback.
- `ComponentSpec.props` and runtime `answer_schema` are already extensible transport records.
  The session view needs no API-model or generated-client change.
- The existing custom-home question maps directly to `/rooms/programme`; the feature changes only
  the typed evidence stored there, through a new questionnaire version.
- Existing tests provide the focused seams: `SemanticRenderer.spec.ts`, `test_definition.py`,
  `test_definition_pack.py`, `test_authoring_workflow.py`, `test_interview_workflow.py`, and
  `test_data_contracts.py`.

## Alternatives Considered

### Continue using `StructuredForm`

- **Rejected**: it would add fixed catalogue/group/status behavior to a generic object-descriptor
  renderer, blur the distinction between ordinary property forms and declared programmes, and
  still leave invalid programme declarations difficult to identify precisely.

### Store display labels as answer values

- **Rejected**: label changes would alter machine meaning and violate stable identifier rules.

### Add custom-home branches to the session engine

- **Rejected**: mapping, answer validation, and projection are already generic. Domain-specific
  runtime behavior would violate the output-contract and typed-UI boundaries.

### Retain Advanced JSON for malformed declared programmes

- **Rejected**: declared-but-unrenderable components are an authoring contract error, not a
  respondent advanced-input scenario.