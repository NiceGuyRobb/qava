# Component Presentation Contract

This internal contract travels in existing `ComponentSpec.props`; it adds no endpoint or OpenAPI
change.

## Supported Parents

| Parent | Expected answer shape | Fields |
| --- | --- | --- |
| `structured_form` | Object | `props.fields` |
| `repeatable_group` | Array of objects | `props.fields` |

## Field Example

```json
{
  "key": "ceiling_preferences",
  "label": "Ceiling preferences",
  "component": "multi_select",
  "options": [{ "value": "raised", "label": "Raised ceilings" }],
  "help_text": "Choose every preference that applies."
}
```

The renderer submits option values, never labels.

## Measurement Example

```json
{
  "key": "target_area",
  "label": "Approximate finished living area",
  "component": "measurement",
  "unit_options": ["sq_ft", "sq_m"]
}
```

The corresponding answer-schema property is an object with required numeric `value` and enum `unit`.

## Rules

1. Keys and labels are non-empty; keys are unique.
2. Nested components are renderer-supported and schema-compatible.
3. Selects require usable options; multi-select requires an array value shape.
4. Measurement requires an object shape and compatible units.
5. An absent field declaration permits advanced JSON. A malformed or unsupported declaration blocks publication rather than silently falling back to JSON.
6. Help/examples cannot change submitted values.