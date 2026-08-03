# Research: Structured Input UX

## Decisions

1. **Extend the existing descriptor renderer.** `registry.ts` already derives typed renderer props,
   and `NestedFieldList.vue` already recurses through nested objects/collections. Add
   `multi_select` and `measurement` there; do not build a new JSON-to-form system.
2. **Use checkbox semantics for nested multi-select.** `ChoiceField.vue` already implements stable
   ID checkbox selection. Chip-only styling is deferred because it does not improve value capture.
3. **Make measurement shape explicit.** A measurement is a declared object with numeric `value` and
   declared `unit`; the answer schema defines it. Do not emit display strings or convert units.
4. **Keep JSON as advanced input only.** An absent structured declaration permits the existing JSON
   editor; a complete declaration must render controls. Label the editor as advanced.
5. **Validate at the existing authoring gate.** Add compatibility issues in `domain/definition.py`,
   used by `compile_draft` and `validate_publication`, so guided updates, raw replacement, and
   publish share one deterministic validation path.
6. **Defer duplicate and reorder.** Existing packs do not justify them; reorder needs an explicit
   ordering contract and keyboard-accessible movement semantics.

## Findings

- No FastAPI route, API model, OpenAPI output, generated client, persistence record, migration,
  mapping, evaluator, projection, or health rule needs to change.
- `ComponentSpec.props` remains an extensible existing transport object; catalog and draft
  validation provide authoring safety without an API change.
- Focused checks: `SemanticRenderer.spec.ts`, `test_definition.py`,
  `test_authoring_workflow.py`, and `test_data_contracts.py`.