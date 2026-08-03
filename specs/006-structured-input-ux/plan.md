
# Implementation Plan: Structured Input UX

**Branch**: `006-structured-input-ux` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

## Summary

Extend existing Vue structured renderers to support nested `multi_select` and `measurement`, and
label raw JSON as an advanced fallback. Add component-declaration validation to the existing draft
compilation/publication gate. This is not a core Qava runtime change: sessions, mappings,
projection, health, persistence, API endpoints, and OpenAPI remain unchanged.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.x / Vue 3.5

**Primary Dependencies**: Existing FastAPI, Pydantic, `jsonschema`, Vue, Vite, Vitest, and Vue Test Utils

**Storage**: Existing SQLite; no migration

**Testing**: pytest/HTTPX, Vitest/Vue Test Utils, existing Playwright smoke flow

**Target Platform**: Existing backend and evergreen desktop/mobile browsers

**Project Type**: Existing FastAPI backend plus Vue SPA

**Constraints**: Preserve declared answer shapes and stable values; add no dependencies, endpoint,
database, mapping, or session-model changes; defer duplicate/reorder and chip-only UI.

**Scale/Scope**: P1 fixes current custom-home structured forms. P2 blocks incompatible presentation
declarations before publication and supports help/example metadata.

## Constitution Check

*GATE: PASS before research and after design.*

| Gate | Result | Evidence |
| --- | --- | --- |
| Output contract | PASS | Existing answer schemas, output targets, and mappings remain authoritative. |
| Simple runtime | PASS | The loop remains published questionnaire plus answers producing next interaction, result, and health. |
| Typed UI | PASS | New controls emit existing declared machine values; no question-specific client rules. |
| Bounded AI | PASS | No AI behavior is added. |
| Continuous projection | PASS | Existing answer submission and recalculation path is unchanged. |
| Explainable health | PASS | Health and attention logic is unchanged. |
| Stable publication | PASS | Existing draft compilation/publish gate gains deterministic declaration issues; versions stay immutable. |

## Project Structure

```text
backend/src/qava/domain/definition.py             # CHANGED: presentation compatibility validation
backend/tests/{unit,integration,contract}/        # CHANGED: validation and publication-gate coverage
frontend/src/components/renderers/
├── registry.ts                                   # CHANGED: typed nested descriptors
├── NestedFieldList.vue                           # CHANGED: multi-select and measurement controls
├── StructuredForm.vue                            # CHANGED: advanced JSON label and shared descriptor use
└── RepeatableGroup.vue                           # CHANGED: advanced JSON label and shared descriptor use
frontend/tests/component/SemanticRenderer.spec.ts # CHANGED: typed emission and fallback coverage
data/components/catalog.v1.json                   # CHANGED: structured props schemas
data/definitions/custom-home-intake/v1/questions/ # CHANGED only where measurement/help metadata is required
```

**Structure Decision**: Preserve the existing backend/frontend/data boundaries. The frontend owns
controls; the backend only validates whether a draft's declared controls are compatible. No new
service, router, model, table, or cross-package abstraction is needed.

## Delivery Slices

| Slice | Scope | Completion gate |
| --- | --- | --- |
| 1. Renderer P1 | Add `multi_select` and `measurement` descriptor support through the shared nested renderer; retain add/remove; label raw JSON advanced. | Existing declared structured/repeated questions render controls rather than a textarea and emit expected values. |
| 2. Definition P1 | Declare the target-area measurement object shape and only needed human-facing metadata. | The checked-in pack compiles without mapping or target changes. |
| 3. Validation P2 | Add compatible/invalid structured declaration checks to `compile_draft` and `validate_publication`; harden checked-in catalog props schema. | Guided and raw drafts surface the same field-specific issue and cannot publish until corrected. |
| 4. Guidance P2 | Render optional field help text/example for supported fields. | Guidance is visible without changing submitted values or server validation. |

## Task Generation Guardrails

- Implement and test Slice 1 before editing definition data or backend validation.
- Use one shared descriptor model for `StructuredForm`, `RepeatableGroup`, and `NestedFieldList`; do not create a generic form editor.
- Keep the existing accessible checkbox semantics for nested multi-select and preserve option IDs.
- Define measurement's exact value/unit object in the answer schema; do not add conversion logic.
- Keep JSON only when no complete supported declaration exists, and label it advanced.
- Validate via `compile_draft` / `validate_publication` so raw and guided authoring share one gate.
- Do not add duplicate/reorder, chip-only styling, migrations, endpoints, or API changes.

## Complexity Tracking

No violations. The only backend work is an additive check in an existing validation seam.
