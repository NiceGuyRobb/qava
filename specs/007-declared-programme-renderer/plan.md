# Implementation Plan: Declared Programme Renderer

**Branch**: `007-declared-programme-renderer` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-declared-programme-renderer/spec.md`

## Summary

Introduce a generic `declared_programme` component contract for grouped, status-based item
selection with optional declared details. The frontend gets a focused renderer that emits one
schema-compatible `selections` object; definition-pack and draft validation reject incomplete or
incompatible declarations before publication. The session API, persistence, mapping, projection,
health, and immutable-version behavior remain unchanged.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.x / Vue 3.5

**Primary Dependencies**: Existing FastAPI, Pydantic, `jsonschema`, Vue, Vite, Vitest, Vue Test
Utils, and Playwright

**Storage**: Existing SQLite repositories and immutable published-questionnaire records; no schema
or migration change

**Testing**: pytest/HTTPX unit, contract, and integration suites; Vitest/Vue Test Utils; existing
Playwright session smoke flow

**Target Platform**: Existing backend and evergreen desktop/mobile browsers

**Project Type**: Existing FastAPI backend plus Vue SPA

**Performance Goals**: Render and update the declared item catalogue with the existing session
interaction responsiveness; no new network round trips per item action

**Constraints**: Preserve direct mapping targets and stable machine values; add no dependencies,
endpoint, OpenAPI, database, session-model, projection, health, or questionnaire-specific engine
logic; do not add item duplication, reordering, free-form items, or unit conversion

**Scale/Scope**: One reusable client component contract, one new Vue renderer, one checked-in
custom-home definition migration, and focused validation/test coverage

## Constitution Check

*GATE: PASS before Phase 0 research and after Phase 1 design.*

| Gate | Result | Evidence |
| --- | --- | --- |
| Output contract | PASS | The existing direct target remains authoritative; the new explicit answer schema constrains only the typed evidence written to that target. |
| Simple runtime | PASS | Runtime remains published questionnaire plus answers producing next interaction, result, and health. The renderer is a client presentation boundary, not a workflow abstraction. |
| Typed UI | PASS | `declared_programme` uses published groups, stable values, labels, statuses, details, and schema-derived props; no custom-home logic is introduced into the client or engine. |
| Bounded AI | PASS | No AI behavior or authority is added. Compatibility validation and unsupported-state fallback are deterministic. |
| Continuous projection | PASS | Accepted objects use the existing answer, mapping, projection, provenance, health, and next-interaction path unchanged. |
| Explainable health | PASS | Existing health rules and attention behavior remain authoritative; invalid declarations block before session execution. |
| Stable publication | PASS | Validation runs during draft compilation/publication. Changed declarations require a new immutable questionnaire version; existing sessions remain pinned. |

**Post-design re-check**: PASS. [research.md](research.md), [data-model.md](data-model.md), and
[contracts/declared-programme.md](contracts/declared-programme.md) preserve all gates without a
complexity exception.

## Project Structure

### Documentation (this feature)

```text
specs/007-declared-programme-renderer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── declared-programme.md
└── tasks.md                  # Created by /speckit.tasks
```

### Source Code (repository root)

```text
backend/
├── src/qava/
│   ├── domain/
│   │   ├── answers.py                         # Generic duplicate programme item validation
│   │   └── definition.py                      # Programme declaration/schema validation
│   └── infrastructure/contracts/
│       ├── definition_pack.py                 # Compile checked-in declaration/schema
│       └── registry.py                        # Catalog and checked-in pack validation
└── tests/
    ├── unit/
    │   ├── test_definition.py
    │   └── test_definition_pack.py
    ├── integration/
    │   ├── test_authoring_workflow.py
    │   └── test_interview_workflow.py
    └── contract/test_data_contracts.py

frontend/
├── src/components/
│   ├── interview/SemanticRenderer.vue         # Existing unsupported boundary; unchanged
│   └── renderers/
│       ├── DeclaredProgramme.vue              # New domain-neutral programme renderer
│       └── registry.ts                        # Component registration and prop derivation
└── tests/component/SemanticRenderer.spec.ts

data/
├── components/catalog.v1.json                 # Declared programme props schema
└── definitions/custom-home-intake/v1/questions/rooms.json
                                                # First generic component consumer
```

**Structure Decision**: Preserve the existing backend/frontend/data ownership boundaries. The
frontend owns declared controls; backend domain validation owns compatibility and answer
integrity; the definition pack owns custom-home labels, values, and mapping. No new service,
router, model, table, or cross-package abstraction is needed.

## Delivery Slices

| Slice | Scope | Completion gate |
| --- | --- | --- |
| 1. Contract and definition | Define `declared_programme` props and explicit answer schema; migrate the checked-in consumer to stable values and labels. | Pack compiles and the contract exposes no home-specific runtime behavior. |
| 2. Respondent renderer | Add dedicated typed renderer and registry derivation; preserve the standard unsupported state for malformed contracts. | Grouped controls emit the exact typed `selections` object with no textarea. |
| 3. Authoring validation | Add shared semantic declaration/schema validation and generic duplicate item-answer validation. | Guided/raw drafts and checked-in packs reject incomplete contracts before publication. |
| 4. Runtime verification | Verify session answer direct mapping, revision/recalculation, and immutable-version behavior. | Accepted response projects unchanged at the existing target; v1 sessions stay unchanged. |

## Task Generation Guardrails

- Implement the source declaration and focused renderer contract before broadening validation.
- Keep `declared_programme` generic: no question IDs, output paths, custom-home labels, or domain
  branches in `DeclaredProgramme.vue`, `registry.ts`, or backend domain code.
- Render native accessible controls and preserve values separately from labels.
- Do not add generic JSON-schema rendering or route the component through `StructuredForm`.
- Use `validate_publication` for shared guided/raw/publish validation; use catalog validation for
  checked-in pack props; avoid duplicated validation rules where a small shared helper suffices.
- Retain Advanced JSON only for genuinely unconstrained generic objects. A malformed declared
  programme is unsupported, not unconstrained.
- Keep APIs, generated OpenAPI, database schema, mappings, projection, health, and session records
  unchanged.
- Validate via the focused frontend renderer, definition-pack, authoring, contract, and interview
  tests before broader suites.

## Complexity Tracking

No violations. A dedicated renderer is justified because the published contract represents a
fixed grouped catalogue with status and item-detail semantics, which ordinary object-property
descriptors cannot express without becoming a less clear generic form editor.
