# Data Model: Structured Input UX

## Unchanged

- **Published questionnaire**: immutable/versioned; contains component specs and answer schemas.
- **Session answer**: server-validated against its declared answer schema.
- **Result, provenance, health, readiness**: existing recalculation after an accepted answer.

## Structured Field Declaration

| Field | Rule |
| --- | --- |
| `key` | Required stable property name; non-empty and unique in its containing declaration. |
| `label` | Required respondent-facing text; never stored as a machine value. |
| `component` | Supported text, number, boolean, select, multi-select, or measurement control. |
| `options` | Required for selects; option values are the stable submitted IDs. |
| `unit_options` | Required for constrained measurements; values are stable unit IDs. |
| `help_text`, `example` | Optional presentation-only guidance. |

## Derived Renderer Descriptor

Client-only, non-persistent descriptors: `string`, `number`, `boolean`, `select`, `multi_select`,
`measurement`, `group`, and `collection`. Measurement emits the exact declared value/unit object.

## Compatibility Issue

A draft validation issue contains a stable code, author-facing message, and question/field pointer.
It covers unsupported nested components, missing options, duplicate keys, and answer-shape mismatch.
Issues update with drafts and block publication; they do not affect published versions or sessions.